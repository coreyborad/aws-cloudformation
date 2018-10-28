# coding: utf-8
import os
import sys
import boto3
import yaml
import datetime
import subprocess
import fileinput
import time


class IaCInstallUtils(object):
    def __init__(self, config, build_type):
        self._aws_access_key_id = config['aws_access_key_id']
        self._aws_secret_access_key = config['aws_secret_access_key']
        self._aws_region_name = config['aws_region_name']
        self._cf = self._get_cf()
        self._cf_resource = self._get_cf_resource()
        self._localpath = os.path.dirname(os.path.abspath(__file__)) + "/"+ build_type
        self._settings = {"Name":config["Name"],"Stack":config["Stack"]}

    def _log(self, message):
        print "%s %s" % ('['+str(datetime.datetime.now())+']', message)

    # 取得CF clinet obj
    def _get_cf(self):
        try:
            cf = boto3.client(
                'cloudformation',
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._aws_region_name)
            return cf
        except:
            self._log('Create cf client failed!')
            os._exit(1)

    # 取得CF resource
    def _get_cf_resource(self):
        try:
            session = boto3.Session(
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._aws_region_name)
            cf_resource = session.resource('cloudformation')
            return cf_resource
        except:
            self._log('Create cf resource failed!')
            os._exit(1)

    def _create_stack(self, stack):
        # 處理Tag
        tags = []
        for tag in stack["Tag"]:
            for k, v in tag.items():
                tags.append({
                    "Key": k,
                    "Value": v
                })
        tags.append({
            "Key": "Name",
            "Value": self._settings["Name"]
        })
        # 處理參數
        parameters = []
        if stack["Parameters"] is not None:
            for parameter in stack["Parameters"]:
                for k, v in parameter.items():
                    parameters.append({
                        'ParameterKey': k,
                        'ParameterValue': v
                    })
        with open(self._localpath + '/cloudformation/' + stack["FileName"]) as f:
            self._cf.create_stack(
                StackName=self._settings["Name"]+"-"+stack["StackSubName"],
                TemplateBody=f.read(),
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'],
                Tags=tags
            )
            return self._settings["Name"]+"-"+stack["StackSubName"]

    def _check_stack_status(self, stack_name):
        stack = self._cf_resource.Stack(stack_name)
        while True:
            self._log('Check status on' + stack_name)
            if stack.stack_status == 'CREATE_COMPLETE':
                return True
            elif stack.stack_status == 'ROLLBACK_COMPLETE':
                self._log('Fail on' + stack_name)
                exit(0)
            stack = self._cf_resource.Stack(stack_name)
            time.sleep(10)

    def launch(self):
        self._log('LaunchIac')
        for stack in self._settings["Stack"]:
            stack_name = self._create_stack(stack)
            self._check_stack_status(stack_name)
            self._log(stack_name + 'Done')


def main():
    try:
        if sys.argv[1] == "aws":
            build_type = "aws"
        elif sys.argv[1] == "lab":
            build_type = "aws_lab"
        else:
            print "Please input correct type"
            exit(0)
    except:
        print "Please input correct type"
        exit(0)

    config = yaml.load(open(os.path.dirname(os.path.abspath(__file__)) + '/'+build_type+'/config.yaml'))

    utils = IaCInstallUtils(config, build_type)
    utils.launch()


if __name__ == "__main__":
    main()
