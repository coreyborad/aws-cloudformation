# coding: utf-8
import os
import sys
import boto3
import yaml
import datetime
import subprocess
import threading

class ProgressPercentage(object):
    def __init__(self, file):
        self._filename = file.get('Key')
        self._size = float(file.get('Size'))
        if self._size <= 0:
            self._size = 1
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()
            if int(percentage) >= 200:
                print "\n%s %s" % (
                    '['+str(datetime.datetime.now())+']', "Copy finish")


class ReleaseUtils(object):
    def __init__(self, aws_access_key_id, aws_secret_access_key, bucket_name,
                 bucket_folder_path, lab_bucket_name):
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._bucket_name = bucket_name
        self._bucket_folder_path = bucket_folder_path
        self._lab_bucket_name = lab_bucket_name
        self._s3 = self._get_s3()
        self._s3_resource = self._get_s3_resource()

    def _log(self, message):
        print "%s %s" % ('['+str(datetime.datetime.now())+']', message)

    # 取得S3 clinet obj
    def _get_s3(self):
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key)
            return s3
        except:
            self._log('Create s3 client failed!')
            os._exit(1)
    
    # 取得S3 clinet obj
    def _get_s3_resource(self):
        try:
            session = boto3.Session(
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key)
            s3_resource = session.resource("s3")
            return s3_resource
        except:
            self._log('Create s3 client failed!')
            os._exit(1)
    
    def _copy_image(self, dist):
        paginator = self._s3.get_paginator('list_objects')
        for result in paginator.paginate(Bucket=self._lab_bucket_name, Delimiter='/', Prefix=dist):
            if result.get('CommonPrefixes') is not None:
                for subdir in result.get('CommonPrefixes'):
                    self._copy_image(subdir.get('Prefix'))
            if result.get('Contents') is not None:
                for file in result.get('Contents'):
                        source = {'Bucket':self._lab_bucket_name, 'Key':file.get('Key')}
                        self._s3.copy(source, self._bucket_name, file.get('Key'), Callback=ProgressPercentage(file))

    def release(self):
        self._log('Start release file to s3')
        self._copy_image(self._bucket_folder_path)


def main():
    config = yaml.load(open(os.path.dirname(os.path.abspath(__file__))+'/config.yaml'))
    utils = ReleaseUtils(config['aws_access_key_id'], config['aws_secret_access_key'],
                         config['bucket_name'], config['bucket_folder_path'], config['lab_bucket_name'])
    utils.release()


if __name__ == "__main__":
    main()
