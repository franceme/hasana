from __future__ import print_function
import os, sys, pwd, json, asana, datetime
from datetime import date, timedelta
from six import print_
import funbelts as ut

def user_select_option(message, options, chosen_option:int = None):
    if chosen_option is None:
        option_lst = list(options)
        print_(message)
        for i, val in enumerate(option_lst):
            print_(i, ': ' + val['name'])
        index = int(input("Enter choice (default 0): ") or 0)
    else:
        index = chosen_option
    return option_lst[index]

class masana(object):
    def __init__(self,access_token:str=None,project_choice:str=None):
        self.client = asana.Client.access_token(access_token)

        self.current_project = None
        self.project = None

        self.current_workspace = None
        self.workspace = None

        self.current_user = self.client.users.me()
        self.user = self.current_user['gid']
        
        self.added_tasks = {}
        if project_choice:
            self.current_workspace = list(self.client.workspaces.find_all())[0]
            self.workspace = self.current_workspace['gid']
            
            self.current_project = list(self.client.projects.find_all({
                'workspace':self.workspace
            }))[0]
            self.project = self.current_project['gid']

    def pick_workspace(self, choice:int):
        self.current_workspace = list(self.client.workspaces.find_all())[choice]
        self.workspace = self.current_workspace['gid']
        return self.current_workspace
    def default_workspace(self):
        return self.pick_workspace(0)

    def pick_project_string(self,choice:str):
        #https://developers.asana.com/docs/get-multiple-projects
        if self.current_workspace != None:
            project = None
            for proj in self.client.projects.get_projects({
                'workspace': self.workspace
            }):
                if proj['name'] == choice:
                    project == proj

            if project is not None:
                self.current_project = project
                self.project = project['gid']
                
        return self.current_project
    def pick_project(self,choice:int):
        if self.current_workspace != None:
            self.current_project = list(self.client.projects.find_all({
                'workspace':self.workspace
            }))[choice]
            self.project = self.current_project['gid']
        return self.current_project
    def default_project(self):
        return self.pick_project(0)

    def defaults(self):
        self.default_workspace()
        self.default_project()

    def delete(self, task_id):
        self.client.tasks.delete_task(task_id)

    def tasks(self):
        if self.current_workspace == None or self.current_project == None:
            return []
        return list(self.client.tasks.get_tasks_for_project(self.project))

    def add_task(self, name:str, notes:str=None, due_day:str=None, due_time:str=None, sub_task_from:int=None):
        if self.current_workspace == None or self.current_project == None:
            return None
        
        if due_day is not None or due_time is not None:
            current_date = str(datetime.datetime.utcnow().isoformat()).split('T')[0]
            due_day = due_day or current_date

            if due_time is not None:
                #https://stackoverflow.com/questions/12691081/from-a-timezone-and-a-utc-time-get-the-difference-in-seconds-vs-local-time-at-t
                local = datetime.datetime.now()
                utc = datetime.datetime.utcnow()
                diff = int((local - utc).days * 86400 + round((local - utc).seconds, -1))
                hours = datetime.timedelta(seconds=diff).hour

                due_time = f"{due_time.hour + hours}:{due_time.minutes}:{due_time.seconds}.000"
            else:
                due_time = "22:00:00.000"

            due_date = f"{due_day}T{due_time}Z"
        else:
            due_date = None
        print(due_date)
        
        #Examples
        #https://github.com/Asana/python-asana/tree/master/examples
        task = None

        if False:
            for tag in tags:
                #https://developers.asana.com/docs/create-a-tag
                self.client.tags.create_tag(self.workspace, tag)

        if sub_task_from:
            #https://developers.asana.com/docs/create-a-subtask
            try:
                task_id = self.client.tasks.create_subtask_for_task(sub_task_from,{
                    'name': name,
                    'assignee':self.user,
                    'approval_status': 'pending',
                    #'tags':tags,
                    'notes':notes,
                    'workspace':self.workspace,
                    'projects': [self.project],
                    'due_at':due_date
                }, opt_fields=['gid'])
                task = self.client.tasks.get_task(task_id['gid'])
            except Exception as e:
                print(f"!Exception {e}")
                pass
        else:
            task_id = None
            try:
                #https://developers.asana.com/docs/create-a-task
                #https://github.com/Asana/python-asana/blob/master/asana/resources/tasks.py#L38
                task_id = self.client.tasks.create_in_workspace(
                    self.workspace,
                    {
                       'assignee':self.user,
                       'name':     name,
                       'notes':    notes,
                       'projects': [self.project],
                       'due_at':due_date
                    },
                    opt_fields=['gid']
                )['gid']
            except Exception as e:
                print(f">Exception {e}")
                pass
            if task_id is None:
                return None

            if False: #Just in case manually searching searching
                task = None
                try:
                    for found_task in tasks:
                        found_task = self.client.tasks.get_task(look_task['gid'])
                        if look_task['resource_type'] == 'task' and look_task['name'] == name and found_task['notes'] == notes:
                            task = found_task
                except Exception as e:
                    print(f"?Exception {e}")
                    pass
                if task is None:
                    return None
            else:
                print(f"Current Task ID {task_id}")
                task = self.client.tasks.get_task(task_id)

            #https://developers.asana.com/docs/update-a-task
            try:
                self.client.tasks.update_task(task_id,
                    {
                        'approval_status': 'pending',
                        #'tags':tags,
                        'notes':notes,
                        'workspace':self.workspace,
                    })
            except Exception as e:
                print(f"$Exception {e}")
                pass
        
        if task is not None:
            self.added_tasks[task['gid']] = task

        return task
    
    def add_task_nextdays(self, name:str, notes:str=None, in_x_days:int=None, due_time:str=None, sub_task_from:int=None):
        current_day = datetime.datetime.utcnow()
        set_day = current_day + datetime.timedelta(days=in_x_days)

        year = set_day.year if set_day.year > 10 else f"0{set_day.year}"
        month = set_day.month if set_day.month > 10 else f"0{set_day.month}" 
        day = set_day.day if set_day.day > 10 else f"0{set_day.day}" 
        nice_day = f"{year}-{month}-{day}"

        return self.add_task(name=name, notes=notes, due_day=nice_day,due_time=due_time,sub_task_from=sub_task_from)