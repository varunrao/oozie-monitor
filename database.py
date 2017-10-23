import parser

__author__ = 'A556504'
#!/usr/bin/env python
import sqlite3
import rest_service
import json
import urllib2
from datetime import date, timedelta
import time
import re

class DatabaseService:

    def __init__(self):
        self.sqlite_file = 'database-files/bigred.sqlite'
        self.table_name = 'jobs'

        self.serviceImpl = rest_service.Runner(10)
        self.serviceImpl.initilize("job.properties",  "knoxPasswordFile.txt")

    def getAllJobs(self, startDate):
        self.conn = sqlite3.connect(self.sqlite_file)
        self.c = self.conn.cursor()
        d = date.today() - timedelta(days=7)
        self.c.execute("SELECT * from jobs where " +
                        " substr(start_time,13,4)|| " +
                        " CASE WHEN (  substr(start_time,9,3)   = 'Jan') THEN ('01') ELSE '' END " +
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Feb') THEN ('02') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Mar') THEN ('03') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Apr') THEN ('04') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'May') THEN ('05') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Jun') THEN ('06') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Jul') THEN ('07') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Aug') THEN ('08') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Sep') THEN ('09') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Oct') THEN ('10') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Nov') THEN ('11') ELSE '' END "+
                        " || CASE WHEN (  substr(start_time,9,3)   = 'Dec') THEN ('12') ELSE '' END ||substr(start_time,6,2) > '"+startDate+"'")
        all_rows = self.c.fetchall()
        #returnedString = str(all_rows).replace("u\"", "\"").replace("u\'", "\'")
        jobs_as_dict = []
        for job in all_rows:
            job_as_dict = {
                'job_id' : job[0],
                'start_time' : job[1],
                'end_time' : job[2],
                'status': job[3],
                'name' : job[4],
                'message' : job[5],
                'user' : job[6],
                'run' : job[7],
                'type' : job[8]
            }
            jobs_as_dict.append(job_as_dict)
        self.conn.close()
        return str(jobs_as_dict).replace("u\"", "\"").replace("u\'", "\'").replace("'", "\"")

    def getOozieJobActions(self, jobId):
        self.conn = sqlite3.connect(self.sqlite_file)
        self.c = self.conn.cursor()
        self.c.execute("select * from oozie_job_action_info where job_id=" + jobId)
        all_rows = self.c.fetchall()
        jobs_action_dict = []
        for job in all_rows:
            job_action_dict = {
                'job_id' : job[0],
                'action_name' : job[1],
                'start_time' : job[2],
                'end_time': job[3],
                'message': job[4],
                'type' : job[5],
                'url' : job[6],
                'status' : job[7],
                'external_status' : job[8],
                'externalId' : job[9]
            }
            jobs_action_dict.append(job_action_dict)
        self.conn.close()
        return str(jobs_action_dict).replace("u\"", "\"").replace("u\'", "\'").replace("'", "\"")

    def checkJobExists(self, jobId):
        #self.conn = sqlite3.connect(self.sqlite_file)
        #self.c = self.conn.cursor()
        self.c.execute("select * from jobs where job_id='" + jobId + "' and status != 'RUNNING'")
        all_rows = self.c.fetchone()
        if all_rows != None and len(all_rows) > 0:
            return True
        return False

    def addRunningJobs(self, jobsToProcess):
        if len(jobsToProcess) == 0 or jobsToProcess['jobs'] == None:
            jobsToProcess = {};
            jobsToProcess['jobs']={};
            jobsToProcess['jobs']['job']=[]

        #self.conn = sqlite3.connect(self.sqlite_file)
        #self.c = self.conn.cursor()
        self.c.execute("select * from ( " +
                       "select 'oozie:launcher'||'='||name||'='||A.job_id name, B.externalId from jobs A, " +
                       "(select externalId,job_id from oozie_job_action_info) B " +
                       " where A.status = 'RUNNING' " +
                        " and A.job_id = B.job_id " +
                        " and B.externalId != '-') C group by C.name ");
        all_rows = self.c.fetchall()
        index = len(jobsToProcess['jobs']['job'])

        for row in all_rows:
            jobsToProcess['jobs']['job'].append({'name': row[0], 'id': row[1]});
        return jobsToProcess

    def loadData(self):
        # A) Inserts an ID with a specific value in a second column
        self.conn = sqlite3.connect(self.sqlite_file)
        self.c = self.conn.cursor()
        try:

            self.c.execute("select value from meta_data where key='lastrun'")
            all_rows = self.c.fetchone()

            lastRun = all_rows[0]
            currTime = int(round(time.time() * 1000))

            jobHistory = self.serviceImpl.getJobHistoryV2("startedTimeBegin="+lastRun+"&queue=etl&user=SVBIGRED")
            if True:
                json_JobHistory = json.loads(jobHistory)
                json_JobHistory = self.addRunningJobs(json_JobHistory)
                if json_JobHistory['jobs'] != None:
                    for jobInfo in json_JobHistory['jobs']['job']:
                        jobName = jobInfo['name']
                        if None != re.search("oozie:launcher", jobName) and None == re.search("_issue", jobName):

                            jobHistoryInfo = self.serviceImpl.getJobHistoryInfo(jobInfo['id'])
                            json_JobHistoryInfo = json.loads(jobHistoryInfo)
                            if not 'RemoteException' in json_JobHistoryInfo:
                                jobName = json_JobHistoryInfo['job']['name']
                                oozieJobId = str(jobName).split("=")[-1]
                                #Oozie job type
                                if None != re.search("oozie:launcher", jobName) and None == re.search("_issue", jobName):

                                    if False == self.checkJobExists(oozieJobId):
                                        oozieJobDetails = self.serviceImpl.getOozieJobInfo(str(oozieJobId));
                                        json_oozieJobDetails = json.loads(oozieJobDetails)
                                        #Insert Job info
                                        insertSQL= "(job_id, start_time, end_time, status, name, message, user, run_number, type) VALUES "\
                                          "('" + oozieJobId +"', '" + str(json_oozieJobDetails['startTime']) +"','"+ str(json_oozieJobDetails['endTime']) +"', '" +\
                                          str(json_oozieJobDetails['status']) + "','"+ str(json_oozieJobDetails['appName']) +"','" + str(json_oozieJobDetails['toString']) +"','"+ \
                                                   str(json_oozieJobDetails['user']) + "','"+ str(json_oozieJobDetails['run']) +"', 'oozie')"
                                        insertSQL = str(insertSQL).replace("$", "").replace("{", "").replace("}", "")
                                        insertSQL = "INSERT or replace INTO {tn} " +  insertSQL
                                        self.c.execute(insertSQL.format(tn=self.table_name))

                                        #Insert Job details
                                        for action in json_oozieJobDetails['actions']:
                                            insertOozieDetails = "Insert or replace into oozie_job_action_info (job_id, action_name, start_time, end_time, message, type, url, status, external_status, externalId) " \
                                                         "values ('"+oozieJobId+"','"+str(action['name'])+"','"+str(action['startTime'])+"','"+str(action['endTime'])+"', '"+\
                                                             str(action['toString'])+"','"+str(action['type'])+"','"+str(action['consoleUrl'])+"','"+str(action['status'])+"','"+str(action['externalStatus'])+"','"+\
                                                             str(action['externalId'])+"')"
                                            insertOozieDetails = str(insertOozieDetails).replace("$", "").replace("{", "").replace("}", "")
                                            #print json_oozieJobDetails
                                            self.c.execute(insertOozieDetails)
                                            self.conn.commit()
                                else:
                                    print "skipping jobName: " + jobName

        except sqlite3.IntegrityError:
            print('ERROR: ID already exists in PRIMARY KEY column')

        #print jobInfo

        #c.execute("SELECT * FROM {tn}".\
        #        format(tn=table_name))
        #all_rows = c.fetchall()
        #print('1):', all_rows)
        self.c.execute("Insert or replace into meta_data (key, value) values ('lastrun','" + str(currTime) + "')")

        self.conn.commit()

        # Closing the connection to the database file
        self.conn.close()

if __name__ == '__main__':
    try:
        database_service = DatabaseService()
        #database_service.loadData()
        for job in database_service.getAllJobs():
            print job[0]
    except IndexError:
        print "Invalid arguments: python oozie_admin_client.py <path-to>job.properties <poll-interval> <path-to-password-file>"
