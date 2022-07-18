from __future__ import print_function
import os, sys, pwd, json, asana, datetime,time
from datetime import date, timedelta
from datetime import datetime as sub
from dateutil.parser import *
import pytz
from six import print_
import funbelts as ut

est =  pytz.timezone('US/Eastern')

class masana(object):
    def __init__(self,access_token:str=None,workspace_choice:str="Personal", project_choice:str=None):
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
        self._tasks = []
        self._full_tasks = []
        
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
    @property
    def old_priorities(self):
        if self._priority == []:
            #https://developers.asana.com/docs/get-a-workspaces-custom-fields
            self._priority = [x for x in list(self.client.custom_fields.get_custom_fields_for_workspace(self.workspace)) if x['name'] == 'Priority']['enum_options']
        return self._priority
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
            self._projects = list(self.client.projects.get_projects({'workspace':self.workspace}))
        return self._projects
    def add_project(self, project:str):
        #https://developers.asana.com/docs/create-a-project
        result = self.client.projects.create_project({
            'name':project,
            'public':False,
            'owner':self.user,
            'default_view':'list',
            'workspace':self.workspace
        })
        self._projects += [result]
        return result
    def get_project(self,project:str):
        #https://developers.asana.com/docs/get-multiple-projects
        if project is not None and self.current_workspace != None:
            found = None
            #https://book.pythontips.com/en/latest/for_-_else.html
            for proj in self.projects:
                if proj['name'] == project:
                    found = proj
                    break
            else:
                found = self.add_project(project)
            return found
        return None
    def del_project(self,project:str=None,project_gid:num=None, log:bool=False):
        """
        https://developers.asana.com/docs/delete-a-project
        """
        current_project = self.get_project(project)
        if current_project and not project_gid:
            project_gid = current_project['gid']

        if project_gid is not None:
            self.client.projects.delete_project(project_gid)
            return True
        else:
            if log:
                print("No Project information is passed")
            return False
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
    def refresh_tasks(self):
        self.tasks(True)
    @property
    def mytasks(self):
        return self.tasks(False)
    def tasks(self, refresh:bool):
        if self.current_workspace == None or self.current_project == None:
            self._tasks = []
        elif self._tasks == [] or refresh:
            self._tasks = list(self.client.tasks.get_tasks_for_project(self.project))
        return self._tasks
    def full_tasks(self, fields=[], log=False):
        try:
            return list(self.client.tasks.get_tasks({
                'assignee': self.user,
                'workspace':self.workspace,
                'opt_fields':fields
            }))
        except Exception as e:
            if log:
                print(e)
            return []
    def tasks_by_date(self, date:datetime.datetime, completed=False,fields=[],log=False):
        """
        https://developers.asana.com/docs/search-tasks-in-a-workspace

        https://stackoverflow.com/questions/2150739/iso-time-iso-8601-in-python
        https://stackoverflow.com/questions/4460698/python-convert-string-representation-of-date-to-iso-8601
        """
        output = []
        try:
            if log:
                print("Looking for dasks due by " + date.isoformat())
            
            if False: #SEARCH IS PREMIUM ONLY
                output = list(self.client.tasks.search_tasks_for_workspace(self.workspace, {
                    'due_by': str(date.isoformat())
                }))
            else:
                #https://developers.asana.com/docs/get-multiple-tasks
                """
                Mass getting and manually filtering
                """
                flag = False
                if log:
                    print('[',end='',flush=True)
                for itr, task in enumerate(self.full_tasks(fields=['due_at','due_on','completed']+fields,log=log)):
                    date = date.astimezone(est)

                    if task['due_on'] is not None:
                        #due_on = sub.strptime(task['due_on'], '%Y-%m-%d')
                        due_on = parse(task['due_on']).astimezone(est) #.strptime(task['due_on'], '%Y-%m-%d')
                    else:
                        due_on = None
                    if task['due_at'] is not None:
                        due_at = parse(task['due_at']).astimezone(est) #, 'Y-%m-%dT%H:%M:%S.%fZ')##'%Y-%m-%dT%H:%M:%S.000')
                        #due_at = sub.fromisoformat(task['due_at'])#strptime(task['due_at'], '%Y-%m-%dT%H:%M:%S.000')
                    else:
                        due_at = None
                    """
                    datetime. strptime(date_time_str, '%d/%m/%y %H:%M:%S')
                    """
                    if (
                            (due_at is not None and date.replace(hour=0,minute=0) < due_at < date)
                            or 
                            (due_on is not None and date.replace(hour=0,minute=0,second=0) <= due_on <= date)
                        ):
                        if not flag:
                            flag = True
                        if completed is None or completed == task['completed']:
                            output += [task]
                    if log:
                        print('.',end='',flush=True)
                if log:
                    print(']',flush=True)
        except Exception as e:
            if log:
                print(e)
            pass
        return output
    def tasks_by_tonight(self, fields=[],log=False):
        return self.tasks_by_date(date=datetime.datetime.now().replace(hour=23,minute=59),completed=False,fields=fields,log=log)
    def task_by_id(self, id):
        return self.client.tasks.get_task(id)
    def complete_task(self,id,log=False):
        #https://developers.asana.com/docs/update-a-task
        output = False
        try:
            self.client.tasks.update_task(id,{
                'completed':True
            })
        except Exception as e:
            if log:
                print(e)
            pass
        return output
    def add_project_to_task(self, task_gid:int, project_strings=None):
        if task_gid is None or project_strings is None:
            return False
        for string in project_strings:
            if project := self.get_project(string):
                try:
                    """
                    https://developers.asana.com/docs/add-a-project-to-a-task
                    """
                    self.client.tasks.add_project_for_task(task_gid, {
                        'project':project['gid']
                    })
                except Exception as e:
                    print('Issue '+str(e))
                    pass
        return True
    def get_tasks(self, project:str=None, waiting:int=1):
        if self.current_workspace == None:
            return []
        elif self._full_tasks != []:
            return self._full_tasks

        #https://developers.asana.com/docs/get-multiple-tasks
        if project == None:
            tasks = list(self.client.tasks.get_tasks({
                'workspace':self.workspace,
                'assignee':self.user
            }))
        else:
            tasks = list(self.client.tasks.get_tasks_for_project(self.project))

        #https://developers.asana.com/docs/get-a-task
        for x in tasks:
            self._full_tasks += [self.client.tasks.get_task(x['gid'])]
            if waiting > 0:
                print(".",end='',flush=True)
                time.sleep(waiting)
        return self._full_tasks
        """
        return [
                self.client.tasks.get_task(x) for x in tasks
        ]
        """
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
        if self.current_workspace == None or (self.current_project == None and projects == [] and sub_task_from == None):
            return None
        
        if due_day is not None:
            current_date = str(est.localize(datetime.datetime.utcnow()).isoformat()).split('T')[0]
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
                    due_time = "22:00:00"

            #http://strftime.net/
            try:
                due_date = f"{est.localize(due_day).strftime('%Y-%m-%dT%H:%M:%SZ')}"
            except:
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

        current_projects = [self.project] if self.project is not None else [self.get_project(x)['gid'] for x in projects]

        if sub_task_from is not None:
            parent_task = self.client.tasks.get_task(sub_task_from)

            #https://developers.asana.com/docs/create-a-subtask
            try:
                task_id = self.client.tasks.create_subtask_for_task(sub_task_from,{
                    'name': name,
                    'assignee':self.user,
                    'approval_status': 'pending',
                    'notes':notes,
                    'workspace':self.workspace,
                    'projects': [x['gid'] for x in parent_task['projects']],
                    'due_at':sub.strptime(parent_task['due_at'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%dT%H:%M:%SZ')
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
        
        self.add_project_to_task(task['gid'], projects)

        if task is not None:
            self.added_tasks[task['gid']] = task

        return task
    def add_task_nextdays(self, name:str, notes:str=None, in_x_days:int=None, due_day:datetime=None, sub_task_from:int=None, tags=[], projects=[]):
        current_day = datetime.datetime.utcnow()
        if due_day is None:
            due_day = current_day
        
        nice_day = due_day.replace(day=current_day + datetime.timedelta(days=in_x_days))

        return self.add_task(name=name, notes=notes, due_day=nice_day,sub_task_from=sub_task_from, tags=tags, projects=projects)
    def add_reoccuring_task(self, name:str, notes:str=None, for_x_days:int=None, until:str=None, due_date:datetime=None, sub_task_from:int=None, tags=[], projects=[], hour:int=None,minute:int=0,second:int=0, waiting:int=5):
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
            sdate=sdate.replace(hour=hour+diff)
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
                print(f"Waiting for {waiting} seconds")
                time.sleep(waiting)
            else:
                print(day)
        return output
        def easy_add_reoccurring_tasks(self,name:str,notes:str=None,pandas_daterange=None, tags=[], projects=[], waiting:int=5):
            output = []
            for day in pandas_daterange:
                output += [
                    self.add_task(name=name, notes=notes, due_day=day,sub_task_from=sub_task_from, tags=tags,projects=projects)
                ]
                print(f"Waiting for {waiting} seconds")
                time.sleep(waiting)
            return output