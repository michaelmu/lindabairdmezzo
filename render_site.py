import os
from jinja2 import Environment, FileSystemLoader

from datetime import datetime as dt
from pytz import timezone, utc

import gspread

class Render():
    def __init__(self, template_file, sheets_creds):
        self.template_file = template_file
        self.sheets_creds = sheets_creds
        self.sheets = self.sheets_init()
        
    def sheets_init(self):
        # scope = ['https://spreadsheets.google.com/feeds',
        #          'https://www.googleapis.com/auth/drive']
        #creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
        client = gspread.authorize(self.sheets_creds)
        # Return the set of sheets for this google sheets
        return client.open("Website Content")

    def get_timestamp(self):
        return dt.now(tz=utc).astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S PDT')

    def get_year(self):
        return dt.now().strftime("%Y")

    def get_about(self):
        return self.sheets.get_worksheet(0).cell(1, 1).value

    def get_photos(self):
        photos = self.sheets.get_worksheet(1).get_all_values()
        # Split the photos into 4 columns. We're splitting based on
        # if there is a '--' in the cell value in col 1
        idx = []
        for (i, (p, t)) in enumerate(photos):
            if p[:2] == '--':
                idx.append(i)
        return [
            photos[:idx[0]],
            photos[idx[0]+1:idx[1]],
            photos[idx[1]+1:idx[2]],
            photos[idx[2]+1:]
        ]

    def get_recordings(self):
        return self.sheets.get_worksheet(2).get_all_values()

    def get_resume(self):
        return self.sheets.get_worksheet(3).get_all_values()

    def get_engagements(self):
        return self.sheets.get_worksheet(4).get_all_values()

    def render_index(self):
        (template_path, template_file) = os.path.split(self.template_file)
        j2_env = Environment(loader=FileSystemLoader(template_path),
                     trim_blocks=True)
        return j2_env.get_template(template_file).render(
            timestamp=self.get_timestamp(),
            year=self.get_year(),
            about_text=self.get_about(),
            photo_set=self.get_photos(),
            recordings=self.get_recordings(),
            resume=self.get_resume(),
            engagements=self.get_engagements(),
        )
