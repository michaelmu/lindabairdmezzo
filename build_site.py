#!/home/mike/static_website/venv/bin/python3.8

import os
import datetime
import boto3
import glob
import mimetypes
import argparse
from PIL import Image
from configparser import ConfigParser
from render_site import Render
from oauth2client.service_account import ServiceAccountCredentials

class SiteBuilder():

    _css_files = ['style.scss', 'bootstrap.scss']
    _dt_format = '%Y-%m-%d %H:%M:%S'
    _bucket_name = 'lindabairdmezzo.com'
    _gallery_images = 'include/images/gallery/*.jpg'
    _include_files = [
        'index.html',
        'favicon.ico',
        'include/css/*.css',
        'include/js/*.js',
        'include/images/*.jpg',
        'include/images/header/*.jpg',
        'include/fonts/bootstrap/*',
        'include/fonts/icomoon/*',
        'include/fonts/simple-line-icons/*',
    ] + [_gallery_images]


    def __init__(self,
                 base_path,
                 compile_css=False,
                 template_file='index_template.html',
                 config_file=None,
                 aws_creds=None,
                 sheets_creds=None):
        self.base_path = base_path
        self.compile_css = compile_css
        self.template_file = os.path.join(base_path, template_file)
        self.input_path = os.path.join(base_path, 'sass')
        self.output_path = os.path.join(base_path, 'include/css')
        self.s3_access_key = aws_creds["access_key"]
        self.s3_secret_key = aws_creds["secret_key"]
        self.sheets_creds = sheets_creds
        
    def get_last_uploaded(self, ts='ts.txt'):
        ts_file = os.path.join(self.base_path, ts)
        # Get our last upload timestamp
        try:
            with open(ts_file, 'r') as f:
                last_uploaded_raw = f.readlines()[0]
                last_uploaded = datetime.datetime.strptime(last_uploaded_raw, self._dt_format)
        except:
            last_uploaded = datetime.datetime(2000,1,1)
        return last_uploaded

    def set_last_uploaded(self, ts='ts.txt'):
        ts_file = os.path.join(self.base_path, ts)
        tsnow = datetime.datetime.utcnow().strftime(self._dt_format)
        # Get our last upload timestamp
        with open(ts_file, 'w') as f:
            f.write(tsnow)

    def is_fresh_file(self, f):
        # Disabling this for now since we don't have state in Lambda
        #return datetime.datetime.utcfromtimestamp(os.path.getmtime(f)) > self.get_last_uploaded()
        return True

    def render_index(self):
        with open(os.path.join(self.base_path, 'index.html'), 'w') as f:
            f.write(Render(os.path.join(self.base_path, 'index_template.html'), sheets_creds=self.sheets_creds).render_index())

    def css_compile(self):
        import sass
        for f in self._css_files:
            basename, _ = os.path.splitext(f)
            outfname = os.path.join(self.output_path, basename + '.css')
            fname = os.path.join(self.input_path, f)
            if self.is_fresh_file(fname):
                compiletime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                compiled_css = sass.compile(filename=fname)
                with open(outfname, 'w') as of:
                    of.write('// Compiled on {}\n'.format(compiletime))
                    of.write(compiled_css)

    def render_placeholder_image(self, img_path):
        # Convert image file into preview version
        im = Image.open(img_path)
        path = os.path.dirname(img_path)
        path, file_name = os.path.split(img_path)
        if file_name[:2] == '__':
            return
        im.thumbnail((12, 8), Image.LANCZOS)
        im.save(os.path.join(path, "__" + file_name), "JPEG")

    def optimize_gallery(self):
        for img_file in glob.glob(os.path.join(self.base_path, self._gallery_images)):
            if self.is_fresh_file(img_file):
                self.render_placeholder_image(img_file)

    def sync_files(self):
        s3 = boto3.resource('s3',
                            aws_access_key_id=self.s3_access_key,
                            aws_secret_access_key=self.s3_secret_key,
                           )
        nfiles = 0
        for infile in self._include_files:
            for globfile in glob.glob(os.path.join(self.base_path, infile)):
                if self.is_fresh_file(globfile):
                    dest_key = os.path.relpath(globfile, self.base_path)
                    mtype, _ = mimetypes.guess_type(globfile)
                    ext = os.path.splitext(globfile)[1]
                    if mtype is None and ext in ['.woff2', '.ttf', '.woff']:
                        mtype = 'font/{}'.format(ext[1:])
                    elif mtype is None:
                        print("!!!! Not handling type of this file: {} !!!".format(globfile))
                        continue
                    print("{} -> {} ({})".format(globfile, dest_key, mtype))
                    with open(globfile, 'rb') as data:
                        s3.Bucket(self._bucket_name).put_object(Key=dest_key, Body=data, ContentType=mtype)
                    nfiles+=1
        self.set_last_uploaded()
        print("{} files uploaded".format(nfiles))

    def update_site(self, deploy=False):
        self.optimize_gallery()
        if self.compile_css:
            print("Compiling CSS...")
            self.css_compile()
        self.render_index()
        if deploy:
            print("Syncing files to S3...")
            self.sync_files()
        else:
            print("Not deploying to S3...")

if __name__ == '__main__':
    import tempfile
    import json
    import base64
    #path = '/home/mike/static_website/lindabaird'
    #config_file = '/home/mike/static_website/config.ini'
    #sheets_creds_file = '/home/mike/static_website/python-sheets-247605-1f73a99684a9.json'
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", help="deploy the site to S3", action='store_true')
    args = parser.parse_args()
    scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
    sheets_creds_json = base64.b64decode(os.environ["sheets_creds_b64"].encode("utf-8")).decode("utf-8")
    sheets_creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(sheets_creds_json, strict=False))
    if "access_key" in os.environ.keys():
        # Get locally exported creds in test mode
        aws_creds = { 
            "access_key": os.environ["access_key"],
            "secret_key": os.environ["private_key"],
        }
    else:
        raise("You need to make sure access_key and private_key are set in the environment variables")
    # Note that CSS compiling doesn't work on AWS Lambda!
    # This is ok since we really only need to do this when we make changes
    # to the CSS. Then we compile the CSS, check it into Git, and it 
    # will be available to Lambda.
    path = os.path.dirname(__file__)
    if args.deploy:
        SiteBuilder(path, 
            compile_css=True, 
            aws_creds=aws_creds, 
            sheets_creds=sheets_creds
            ).update_site(deploy=True)
    else:
        SiteBuilder(path, 
            compile_css=True, 
            aws_creds=aws_creds, 
            sheets_creds=sheets_creds
            ).update_site()
