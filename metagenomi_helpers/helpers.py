import os
import subprocess
import shlex
import shutil
import boto3
import uuid
import boto3

# will use env AWS_* credentials
s3 = boto3.resource('s3')


def basename(full_name, extensions=[]):
    '''
    Return basename of a path-like string. Works like shell basename with
    extensions.
    :param full_name: full path to perform basename on
    :param ext: array of extensionto remove, if required
    :return: string of the basename
    '''
    bname = full_name.split('/')[-1]
    if len(extensions) > 0:
        for ext in extensions:
            if bname.endswith(ext):
                return(bname[:-len(ext)])
    return(bname)

def download_folder(s3_path, dir_to_dl, dry_run=False):
    '''
    Downloads a folder from s3
    :param s3_path: s3 folder path
    :param dir_to_dl: local path of dir to download to
    :return: dir that was downloaded
    '''

    cmd = f'aws s3 cp --recursive {s3_path} {dir_to_dl}'

    if dry_run:
        print(cmd)
    else:
        subprocess.check_call(shlex.split(cmd))

    return dir_to_dl


def download_file_multi(s3_path_list, dir_to_dl, dry_run=False):
    print(f's3_path_list \n\n{s3_path_list}')
    '''
    Downloads multiple files from s3
    :param s3_path_list: list of s3 object paths
    :param dir_to_dl: local path of dir to download to
    :return: list of local file paths of the downloaded objects
    '''
    local_paths = list()

    seen = dict()
    dupnum = 1
    for s3_path in s3_path_list:
        bucket = s3_path.split('/')[2]
        key = '/'.join(s3_path.split('/')[3:])
        name = key.split('/')[-1]
        if name in seen:
            name = f'{dupnum}_{name}'
            dupnum += 1
        else:
            seen[name] = 1
        local_paths.append(download_file_as(s3_path, dir_to_dl, name, dry_run))

    return(local_paths)


def download_file(s3_path, dir_to_dl, dry_run=False):
    '''
    Downloads a folder from s3
    :param s3_path: s3 object path
    :param dir_to_dl: local path of dir to download to
    :return: local file path of the object downloaded
    '''
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])

    object_name = key.split('/')[-1]
    local_file_name = os.path.join(dir_to_dl, object_name)

    if dry_run:
        print('Fake download')
    else:
        print(f'bucket {bucket} key {key} local_file_name {local_file_name}')
        s3.Object(bucket, key).download_file(local_file_name)
    return local_file_name


def download_file_as(s3_path, dir_to_dl, name, dry_run=False):
    '''
    Downloads a folder from s3 and change its local name
    :param s3_path: s3 object path
    :param dir_to_dl: local path of dir to download to
    :param name: name of file to create
    :return: local file path of the object downloaded
    '''
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])

    object_name = key.split('/')[-1]
    local_file_name = os.path.join(dir_to_dl, name)

    if dry_run:
        print('Fake download')
    else:
        print(f'bucket {bucket} key {key} local_file_name {local_file_name}')
        s3.Object(bucket, key).download_file(local_file_name)
    return local_file_name


def download_pattern(s3_path, dir_to_dl, include, exclude='"*"', dry_run=False):
    '''
    Downloads multiple files from s3 based on include/exclude
    :param s3_path: s3 object path
    :param dir_to_dl: local path of dir to download to
    :return: local path of dir to download to
    '''

    # check include and exclude to be sure they start and end with with ""
    if include[0] != '"':
        if include[-1] != '"':
            include = f'"{include}"'

    dir_to_dl = dir_to_dl.rstrip('/')+'/'

    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])

    cmd = f"aws s3 cp --recursive --exclude={exclude} --include={include} \
          s3://{bucket}/{key} {dir_to_dl}"


    if dry_run:
        print('--- dry run ---')
        print(cmd)

    else:
        subprocess.check_call(shlex.split(cmd))

    return dir_to_dl


def rm_files(s3_path, files, dry_run=False):
    '''
    Removes files on s3 given a path and a list of filenames
    '''

    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])

    for f in files:
        cmd = f'aws s3 rm s3://{bucket}/{key}/{f}'

        if dry_run:
            print('--- dry run ---')
            print(cmd)

        else:
            subprocess.check_call(shlex.split(cmd))


def upload_folder(s3_path, local_folder_path, dry_run=False):
    '''
    Uploads a folder to s3
    :param s3_path: s3 path to upload folder to
    :param local_folder_path: path to local folder
    '''

    cmd = f'aws s3 cp --recursive {local_folder_path} {s3_path}'

    if dry_run:
        print(cmd)
    else:
        subprocess.check_call(shlex.split(cmd))


def upload_file(local_path, s3_path, compress=False, dry_run=False):
    '''
    Uploads a file to s3
    :param local_path: path to local file
    :param s3_path: s3 path to object
    :param compress: compress before uploading?
    :param dry_run: dry run only
    :return: response from the upload file call
    '''
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])

    if compress:
        subprocess.check_call(['pigz', local_path])
        local_path += '.gz'

    if dry_run:
        print('Fake upload')
    else:
        response = s3.Object(bucket, key).upload_file(local_path)
        return response


def generate_working_dir(working_dir_base):
    '''
    Creates a unique working dir to prevent overwrites from multiple containers
    :param working_dir_base: base working dir (e.g. /scratch)
    :return: a uniquely-named subfolder in working_dir_base with a uuid
    '''

    working_dir = os.path.join(working_dir_base, str(uuid.uuid4()))
    # try to make the dir
    try:
        os.mkdir(working_dir)
    except Exception as e:
        # already exists
        return working_dir_base
    return working_dir


def delete_working_dir(working_dir):
    '''
    Delete the working dir
    :param working_dir: working directory
    '''

    try:
        shutil.rmtree(working_dir)
    except Exception as e:
        print(f"Can't delete {working_dir}")


def is_unique_mgid(mg_id, dbname):
    db = boto3.resource('dynamodb')
    tbl = db.Table(dbname)

    response = tbl.get_item(
        Key={
            'mg-identifier': mg_id,
            }
        )

    if 'Item' in response:
        return False

    return True



def submit_job(name, jq, jobdef, params):
    '''
    Submit an AWS Batch job to the defined job queue
    :param name: the job name
    :param jq: the job queue name
    :param jobdef: the job definition string (e.g. mg-usearch-jobdef:4)
    :param params: dict of container overrides key/value pairs
    :return: dict of return information from aws batch command
    '''
