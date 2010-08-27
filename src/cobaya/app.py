###############################################################################
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# any later version.                                                          #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
# Copyright (C) 2010, Lorenzo Gil Sanchez <lgs@yaco.es>                       #
###############################################################################

from os import path

from cobaya.hamster_task import HamsterTask
from cobaya.hamster_db import HamsterDB
from cobaya.config import Config
from cobaya.remote_server import RemoteServer


class CobayaApp(object):

    def __init__(self):
        conf = Config()
        conf.load()
        self.log_file = conf.get_option('hamster.log_file')
        self.ids = []
        if path.exists(self.log_file):
            f = file(self.log_file, 'r')
            self.ids = f.readlines()
        else:
            f = file(self.log_file, 'w')
            f.close()

        self.tasks = get_all_tasks()

        for id in self.tasks:
            str_id = ('%d\n' % id)
            if str_id in self.ids:
                self.tasks[id].remote_sync = True


    def generate_unsynced_data(self):
        data = []
        for id in self.tasks:
            if self.tasks[id].remote_sync == False and \
               self.tasks[id].time != 0.0: # not synced or not finished
                data.append(self.tasks[id].to_dict())
        return data

    def perform_notification(self):
        unsynced_data = self.generate_unsynced_data()

        server = RemoteServer()
        synced_tasks = server.send_tasks(unsynced_data)
        news_id = []
        for task in synced_tasks:
            id = task['task_id']
            news_id.append("%d\n" % id)
            self.tasks[id].remote_sync = True
        f = file(self.log_file, 'a')
        f.writelines(news_id)
        f.close()


def get_all_tasks():
    """Returns a list with every task registred on Hamster.
    """

    db = HamsterDB()
    result = db.query("SELECT id FROM facts")
    db.close_connection()

    fact_list = [x[0] for x in result]
    tasks = {}

    for fact_id in fact_list:
        rt = HamsterTask(fact_id).get_remote_task()
        tasks[rt.task_id] = rt

    print 'Obtained %d tasks' % len(tasks)
    return tasks


def main():
    cob = CobayaApp()

    cob.perform_notification()


if __name__ == '__main__':
    main()

