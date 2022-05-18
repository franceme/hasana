from __future__ import print_function
import os, sys, pwd, json, asana, datetime,time
from datetime import date, timedelta
from six import print_
import funbelts as ut

class masana(object):
    def __init__(self,access_token:str=None,project_choice:str=None, workspace_choice:str="Personal"):
        self.client = asana.Client.access_token(access_token)

        self.current_project = None
        self.project = None

        self.current_workspace = None
        self.workspace = None

        self.current_user = self.client.users.me()
        self.user = self.current_user['gid']
        
        self.added_tasks = {}
        self._tags = []
        self._projects = []
        
        #https://developers.asana.com/docs/custom-fields
        #self._priority = []
        if project_choice and workspace_choice:
            self.current_workspace = [x for x in list(self.client.workspaces.find_all()) if x['name'] == workspace_choice][0]
            self.workspace = self.current_workspace['gid']
            
            self.current_project = [x for x in list(self.client.projects.find_all({
                'workspace':self.workspace
            })) if x['name'] == project_choice][0]
            self.project = self.current_project['gid']
        elif workspace_choice:
            self.current_workspace = [x for x in list(self.client.workspaces.find_all()) if x['name'] == workspace_choice][0]
            self.workspace = self.current_workspace['gid']

    def pick_workspace(self, choice:int):
        self.current_workspace = list(self.client.workspaces.find_all())[choice]
        self.workspace = self.current_workspace['gid']
        return self.current_workspace
    def default_workspace(self):
        return self.pick_workspace(0)

    """
    @property
    def priorities(self):
        if self._priority == []:
            #https://developers.asana.com/docs/get-a-workspaces-custom-fields
            self._priority = [x for x in list(self.client.custom_fields.get_custom_fields_for_workspace(self.workspace)) if x['name'] == 'Priority']['enum_options']
        return self._priority
    """

    @property
    def tags(self):
        if self._tags == []:
            self._tags = list(self.client.tags.get_tags_for_workspace(self.workspace))
        return self._tags

    def add_tag(self, string_name):
        tag = self.client.tags.create_tag({
            'name':string_name,
            'workspace':self.workspace
        })
        self._tags += [tag]
        return tag

    @property
    def projects(self):
        if self._projects == []:
            self._projects = list(self.client.projects.get_projects(self.workspace))
        return self._projects

    def add_project(self, project:str):
        #https://developers.asana.com/docs/create-a-project
        result = self.client.projects.create_project({
            'name':project,
            'public':False,
            'owner':self.user,
            'default_view':'list'
        })
        self._projects += [result]
        return result
    def get_project(self,project:str):
        #https://developers.asana.com/docs/get-multiple-projects
        if self.current_workspace != None:
            found = None
            for proj in self.projects:
                if proj['name'] == project:
                    found == proj
            
            if found is None:
                found = self.create_project(project)
            return found
        return None
            

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

    def add_tags_to_task(self,taskid,tags=[]):
        """
        for tag in tags:
            try:
                #https://developers.asana.com/docs/get-tags-in-a-workspace
                #Identifying Tags
                current_tags = list(self.client.tags.get_tags_for_workspace(self.workspace))
                searched_tag = [x for x in current_tags if x['name'] == tag]
                if len(searched_tag) > 0:
                    found_tag = searched_tag[0]
                else: #https://developers.asana.com/docs/create-a-tag
                    found_tag = self.client.tags.create_tag({
                        'name':tag
                    })
                #https://developers.asana.com/docs/add-a-tag-to-a-task
                self.client.tasks.add_tag_for_task(
                    taskid,
                    {
                        'tag':found_tag['gid']
                    }
                )
            except Exception as e:
                print(f"!!Exception {e}")
                pass
        """
        for tag in tags:
            try:
                searched_tag = [x for x in self.tags if x['name'] == tag]
                if len(searched_tag) > 0:
                    found_tag = searched_tag[0]
                else: #https://developers.asana.com/docs/create-a-tag
                    found_tag = self.add_tag(tag)
                self.client.tasks.add_tag_for_task(
                    taskid,
                    {
                        'tag':found_tag['gid']
                    }
                )
            except Exception as e:
                print(f"!!Exception {e}")
                pass
    def add_task(self, name:str, notes:str=None, due_day:str=None, sub_task_from:int=None, tags=[], projects=[]):
        if self.current_workspace == None or (self.current_project == None and projects == []):
            return None
        
        if due_day is not None:
            current_date = str(datetime.datetime.utcnow().isoformat()).split('T')[0]
            due_day = due_day or current_date

            if False:
                if due_time is not None:
                    #https://stackoverflow.com/questions/12691081/from-a-timezone-and-a-utc-time-get-the-difference-in-seconds-vs-local-time-at-t
                    local = datetime.datetime.now()
                    utc = datetime.datetime.utcnow()
                    diff = int((local - utc).days * 86400 + round((local - utc).seconds, -1))
                    hours = datetime.timedelta(seconds=diff)
                    hours, _ = divmod(hours.seconds, 3600)

                    due_time = f"{due_time.hour + hours}:{due_time.minute}:{due_time.second}.000"
                else:
                    due_time = "22:00:00.000"

            #http://strftime.net/
            due_date = f"{due_day.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        else:
            due_date = None
        
        #Examples
        #https://github.com/Asana/python-asana/tree/master/examples
        task = None

        if False:
            for tag in tags:
                #https://developers.asana.com/docs/create-a-tag
                self.client.tags.create_tag(self.workspace, tag)

        current_projects = [self.project] if self.project is not None else [self.get_project(x) for x in projects]

        if sub_task_from is not None:
            #https://developers.asana.com/docs/create-a-subtask
            try:
                task_id = self.client.tasks.create_subtask_for_task(sub_task_from,{
                    'name': name,
                    'assignee':self.user,
                    'approval_status': 'pending',
                    'notes':notes,
                    'workspace':self.workspace,
                    'projects': current_projects,
                    'due_at':due_date
                }, opt_fields=['gid'])
                task = self.client.tasks.get_task(task_id['gid'])
                self.add_tags_to_task(task_id['gid'], tags)
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
                       'projects': current_projects,
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
                        'notes':notes,
                        'workspace':self.workspace,
                    })
            except Exception as e:
                print(f"$Exception {e}")
                pass
        
            try:
                self.add_tags_to_task(task_id, tags)
            except Exception as e:
                print(f"%>Exception {e}")
                pass
        
        if task is not None:
            self.added_tasks[task['gid']] = task

        return task
    def add_task_nextdays(self, name:str, notes:str=None, in_x_days:int=None, due_day:datetime=None, sub_task_from:int=None, tags=[], projects=[]):
        current_day = datetime.datetime.utcnow()
        if due_day is None:
            due_day = current_day
        
        nice_day = due_day.replace(day=current_day + datetime.timedelta(days=in_x_days))

        return self.add_task(name=name, notes=notes, due_day=nice_day,sub_task_from=sub_task_from, tags=tags, projects=projects)
    def add_reoccuring_task(self, name:str, notes:str=None, for_x_days:int=None, until:str=None, due_date:datetime=None, sub_task_from:int=None, tags=[], projects=[], hour:int=None,minute:int=0,second:int=0):
        output = []

        if due_date is None:
            sdate = datetime.datetime.utcnow()
        else:
            sdate = due_date
        
        #TimeReplace https://stackoverflow.com/questions/12468823/python-datetime-setting-fixed-hour-and-minute-after-using-strptime-to-get-day
        if hour is not None:
            local = datetime.datetime.now()
            utc = datetime.datetime.utcnow()
            diff = int((local - utc).days * 86400 + round((local - utc).seconds, -1))
            sdate=sdate.replace(hour=hour+diff+4)
        if minute is not None:
            sdate=sdate.replace(minute=minute)
        if second is not None:
            sdate=sdate.replace(second=second)

        if for_x_days is not None:
            edate = sdate + datetime.timedelta(days=for_x_days+1)
        else:
            edate = until + datetime.timedelta(days=2)

        range_of_days = [sdate+timedelta(days=x) for x in range((edate-sdate).days)]
        for day in range_of_days:
            if True:
                output += [
                    self.add_task(name=name, notes=notes, due_day=day,sub_task_from=sub_task_from, tags=tags,projects=projects)
                ]
                waiting = 5
                print(f"Waiting for {waiting} seconds")
                time.sleep(waiting)
            else:
                print(day)
        return output