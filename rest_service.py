# !/usr/bin/python
import os
import io
import sys
import json
import urllib2
import base64
import xml.etree.ElementTree as ET
import time
import re


class Runner:
    def __init__(self, poll_interval):
        self.execution_conf = {}
        self.oozie_host = ""
        self.oozie_port = ""
        self.knox_truth = ""
        self.knox_gateway_host = ""
        self.knox_gateway_port = ""
        self.knox_gateway_path = ""
        self.cluster_name = ""
        self.knox_user = ""
        self.knox_password = ""
        self.poll_interval = float(poll_interval)
        self.xml_request_data = ""

    def parse_job_properties(self, job_properties):
        try:
            with io.open(job_properties, 'r') as wf_config:
                content = wf_config.readlines()
        except IOError as e:
            print "Error opening job.properties at %s" % e
            sys.exit(2)
        #build the configuration dictionary
        line_counter = 0
        for line in content:
            line_counter += 1
            if line.strip().startswith("#") or line.strip() == "":
                continue
            try:
                key = line.split("=")[0].strip()
                value = line[line.find("=", 0) + 1:].strip()
                if key == '' or value == '':
                    print "Missing key or value in the job.properties at line %d" % line_counter
                    sys.exit(2)
                #create an array with needed properties for workflow submission
                self.execution_conf[key] = value
            except Exception as e:
                print "Error in loading the job.properties at line %d - %s" % line_counter % e
        min_keys = ["jobTracker", "nameNode", "user.name", "oozie_host", "oozie_port",
                    "knox_truth"]
        for key in min_keys:
            if not key in self.execution_conf:
                print "Missing required configuration key : %s" % key
                sys.exit(2)
            else:
                setattr(self, key, self.execution_conf[key])
        if self.knox_truth == "true":
            for knox_props in ["knox_gateway_host", "knox_gateway_port", "knox_gateway_path", "cluster_name",
                               "knox_user"]:
                if not knox_props in self.execution_conf:
                    print "Missing required configuration key : %s" % knox_props
                    sys.exit(2)
                else:
                    setattr(self, knox_props, self.execution_conf[knox_props])
                    #del self.execution_conf[knox_props]

    def read_password_file(self, path_to_password_file):
        try:
            with io.open(path_to_password_file, 'r') as pwd_file:
                line = pwd_file.readline()
                setattr(self, "knox_password", line.rstrip(' \t\n\r'))
        except IOError as e:
            print "Error opening password file at %s" % e
            sys.exit(2)

    def initilize(self, job_properties, path_to_pwd_file):
        if os.path.isfile(job_properties):
            #instantiate
            #runner = Runner(poll_interval)
            #parse job.properties file into an array
            self.parse_job_properties(job_properties)
            #covert array to xml
            #runner.arr2xml()
            #read password file
            self.read_password_file(path_to_pwd_file)
            #submit oozie workflow - POST request with xml pay-load
            #wf_id = runner.submit_workflow()
            #wf_id = "0001784-140722144336252-oozie-oozi-W"
            keep_running = True
            status = ""
            #wf_id = "0021801-141029175705544-oozie-oozi-W"
            #status = runner.poll(wf_id)
            #print "Workflow: %s  -- Status: %s" % (wf_id, status)
            #sys.exit(0)
        else:
            print "Could not find job.properties"
            sys.exit(1)

    def getJobs(self, jobParams):
        #iterate over submitted workflow and poll the Oozie API for status for every defined poll interval
        #http://d-9zq75y1.test.com:11000/oozie/v1/job/0000173-140321083151873-oozie-oozi-W?show=info

        poll_url = "http://" + self.oozie_host + ":" + self.oozie_port + "/oozie/v1/jobs?filter=%s" % jobParams
        #poll_url = "http://" + self.oozie_host + ":" + self.oozie_port + "/oozie/v1/admin/status"
        if self.knox_truth == "true":
            try:
                poll_url = "https://" + self.knox_gateway_host + ":" + self.knox_gateway_port + "/" + self.knox_gateway_path + "/" + self.cluster_name + "/oozie/v1/jobs?filter=%s" % jobParams
                #poll_url = "https://" + self.knox_gateway_host + ":" + self.knox_gateway_port + "/" + self.knox_gateway_path + "/" + self.cluster_name + "/oozie/v1/jobs?filter=user%3DSVBIGRED"
                request = urllib2.Request(poll_url, headers={"X-XSRF-Header": "valid"})
                base64string = base64.encodestring('%s:%s' % (self.knox_user, self.knox_password))[:-1]
                request.add_header("Authorization", "Basic %s" % base64string)
                json_response = urllib2.urlopen(request).read()
            except Exception as e:
                print "Error connecting to the Oozie server with knox - %s" % e
                sys.exit(2)
        else:
            try:
                request = urllib2.Request(poll_url)
                json_response = urllib2.urlopen(request).read()
            except Exception as e:
                print "Error connecting to the Oozie server - %s" % e
                sys.exit(2)
        #Create a JSON object
        try:
            returnedString = str(json_response).replace("u\"", "\"").replace("u\'", "\'")
            #json_object = json.loads(returnedString)
            #print json_object
            #print json_object['startTime'] + ", " + json_object['endTime']

        except Exception as e:
            print e
            sys.exit(2)
            #LOG.error("Error parsing the JSON from Oozie")
        return returnedString

    def getOozieJobInfo(self, wfid):
        #iterate over submitted workflow and poll the Oozie API for status for every defined poll interval
        #http://d-9zq75y1.test.com:11000/oozie/v1/job/0000173-140321083151873-oozie-oozi-W?show=info

        poll_url = "http://" + self.oozie_host + ":" + self.oozie_port + "/oozie/v1/job/%s?show=info" % wfid
        #poll_url = "http://" + self.oozie_host + ":" + self.oozie_port + "/oozie/v1/admin/status"
        if self.knox_truth == "true":
            try:
                poll_url = "https://" + self.knox_gateway_host + ":" + self.knox_gateway_port + "/" + self.knox_gateway_path + "/" + self.cluster_name + "/oozie/v1/job/%s?show=info" % wfid
                #poll_url = "https://" + self.knox_gateway_host + ":" + self.knox_gateway_port + "/" + self.knox_gateway_path + "/" + self.cluster_name + "/oozie/v1/jobs?filter=user%3DSVBIGRED"
                request = urllib2.Request(poll_url, headers={"X-XSRF-Header": "valid"})
                base64string = base64.encodestring('%s:%s' % (self.knox_user, self.knox_password))[:-1]
                request.add_header("Authorization", "Basic %s" % base64string)
                json_response = urllib2.urlopen(request).read()
            except Exception as e:
                print "Error connecting to the Oozie server with knox - %s" % e
                sys.exit(2)
        else:
            try:
                request = urllib2.Request(poll_url)
                json_response = urllib2.urlopen(request).read()
            except Exception as e:
                print "Error connecting to the Oozie server - %s" % e
                if e.code != 404:
                    sys.exit(2)
                else:
                    return ""
        #Create a JSON object
        try:
            returnedString = str(json_response).replace("u\"", "\"").replace("u\'", "\'")
            #json_object = json.loads(returnedString)
            #print json_object
            #print json_object['startTime'] + ", " + json_object['endTime']

        except Exception as e:
            print e
            sys.exit(2)
            #LOG.error("Error parsing the JSON from Oozie")
        return returnedString

    def getJobHistoryInfo(self, jobId):
        #iterate over submitted workflow and poll the Oozie API for status for every defined poll interval
        #http://d-9zq75y1.test.com:11000/oozie/v1/job/0000173-140321083151873-oozie-oozi-W?show=info

        #startedTimeBegin=%s&limit=1&queue=etl&user=SVBIGRED
        poll_url = "http://d-3zktk02.test.com:19888/ws/v1/history/mapreduce/jobs/%s" % str(jobId)
        print str(jobId)
        try:
            request = urllib2.Request(poll_url)
            json_response = urllib2.urlopen(request).read()
        except Exception as e:
            print "Error connecting to the Oozie server - %s, job_id : %s" % (e, jobId)
            if e.code != 404:
                sys.exit(2)
            else:
                return "{\"RemoteException\":\"Not found\"}";
        #Create a JSON object
        try:
            returnedString = str(json_response).replace("u\"", "\"").replace("u\'", "\'")
            #json_object = json.loads(returnedString)
            #print json_object
            #print json_object['startTime'] + ", " + json_object['endTime']

        except Exception as e:
            print e
            sys.exit(2)
            #LOG.error("Error parsing the JSON from Oozie")
        return returnedString

    def getJobHistoryV2(self, params):
        #iterate over submitted workflow and poll the Oozie API for status for every defined poll interval
        #http://d-9zq75y1.test.com:11000/oozie/v1/job/0000173-140321083151873-oozie-oozi-W?show=info

        #startedTimeBegin=%s&limit=1&queue=etl&user=SVBIGRED
        poll_url = "http://d-3zktk02.test.com:19888/ws/v1/history/mapreduce/jobs?%s" % str(params)

        try:
            request = urllib2.Request(poll_url)
            json_response = urllib2.urlopen(request).read()
        except Exception as e:
            print "Error connecting to the Oozie server - %s" % e
            if e.code != 404:
                sys.exit(2)
            else:
                return "";
        #Create a JSON object
        try:
            returnedString = str(json_response).replace("u\"", "\"").replace("u\'", "\'")
            #json_object = json.loads(returnedString)
            #print json_object
            #print json_object['startTime'] + ", " + json_object['endTime']

        except Exception as e:
            print e
            sys.exit(2)
            #LOG.error("Error parsing the JSON from Oozie")
        return returnedString

    def getJobHistory(self, startTime):
        #iterate over submitted workflow and poll the Oozie API for status for every defined poll interval
        #http://d-9zq75y1.test.com:11000/oozie/v1/job/0000173-140321083151873-oozie-oozi-W?show=info

        #poll_url = "http://d-3zktk02.test.com:19888/ws/v1/history/mapreduce/jobs?queue=etl&finishedTimeBegin=%s" % str(startTime)
        poll_url = "http://d-3zjtk02.test.com:8088/ws/v1/cluster/apps?states=FINISHED&user=SVBIGRED&startedTimeBegin=%s" % str(startTime)

        try:
            request = urllib2.Request(poll_url)
            json_response = urllib2.urlopen(request).read()
        except Exception as e:
            print "Error connecting to the Oozie server - %s" % e
            if e.code != 404:
                sys.exit(2)
            else:
                return "";
        #Create a JSON object
        try:
            returnedString = str(json_response).replace("u\"", "\"").replace("u\'", "\'")
            #json_object = json.loads(returnedString)
            #print json_object
            #print json_object['startTime'] + ", " + json_object['endTime']

        except Exception as e:
            print e
            sys.exit(2)
            #LOG.error("Error parsing the JSON from Oozie")
        return returnedString

    def poll(self, wfid):
        json_object = self.getOozieJobInfo(wfid)
        return json_object["status"]


if __name__ == '__main__':
    #program entry point
    try:
        job_properties = sys.argv[1]
        poll_interval = sys.argv[2]
        path_to_pwd_file = sys.argv[3]
        #instantiate
        runner = Runner(poll_interval)
        runner.initilize(job_properties, path_to_pwd_file);
    except IndexError:
        print "Invalid arguments: python oozie_admin_client.py <path-to>job.properties <poll-interval> <path-to-password-file>"
        sys.exit(1)
