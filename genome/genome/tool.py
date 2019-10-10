# encoding=utf8
from __future__ import unicode_literals
import frappe
import dropbox
import json
import time
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, getdate, add_years, time_diff, get_datetime_str
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import delete_file, get_file, get_files_path
from frappe.integrations.doctype.dropbox_settings.dropbox_settings import upload_file_to_dropbox, get_dropbox_settings, generate_oauth2_access_token_from_oauth1_token, set_dropbox_access_token

import sys
reload(sys)
sys.setdefaultencoding('utf8')

DROPBOX_TARGET = "/Apps/KISSr/mhbu50.kissr.com"

def after_insert_patient(doc, method):
    doc.hash_id = frappe.generate_hash(length=12)
    doc.save()


@frappe.whitelist()
def add_pdf(doc):
    execute(doc)


def execute(doc):
    envelop_name = frappe.generate_hash(length=34)
    shareable_file_name = frappe.generate_hash(length=34)
    lab_test_doc = frappe.get_doc("Lab Test", doc)
    lab_test_doc.envelope_id = envelop_name
    lab_test_doc.save()

    if not frappe.db:
        frappe.connect()

    # upload database
    dropbox_settings = get_dropbox_settings()

    if not dropbox_settings['access_token']:
        access_token = generate_oauth2_access_token_from_oauth1_token(
            dropbox_settings)

        if not access_token.get('oauth2_token'):
            return 'Failed backup upload', 'No Access Token exists! Please generate the access token for Dropbox.'

        dropbox_settings['access_token'] = access_token['oauth2_token']
        set_dropbox_access_token(access_token['oauth2_token'])

    dropbox_client = dropbox.Dropbox(dropbox_settings['access_token'])
    # print "befor upload"
    upload_file_to_dropbox(get_file_path(
        lab_test_doc.lab_test_result_file[7:]), DROPBOX_TARGET, dropbox_client)
    upload_file_to_dropbox(get_file_path(
        lab_test_doc.arabic_result_file[7:]), DROPBOX_TARGET, dropbox_client)

    html_data1 = frappe.render_template("templates/envlop.html",
                                        {"patient_name": lab_test_doc.arabic_first_name, "disease": lab_test_doc.disease_description, "file1": lab_test_doc.lab_test_result_file[7:], "file2": lab_test_doc.arabic_result_file[7:],
                                         "shareable_file_name": shareable_file_name, "hash_id": lab_test_doc.hash_id})
    envlop_file = save_generated_file(html_data1, envelop_name)
    upload_file_to_dropbox(get_file_path(envlop_file), DROPBOX_TARGET, dropbox_client)

    disease_doc = frappe.get_doc("Diseases", lab_test_doc.disease)
    html_data2 = frappe.render_template("templates/shareable_file1.html",
                                        {"disease": disease_doc.name,
                                         "disease_story": disease_doc.description,
                                         "html_pattern": disease_doc.html_pattern,
                                         "hash_id": lab_test_doc.hash_id})

    shareable_file = save_generated_file(html_data2, shareable_file_name)
    upload_file_to_dropbox(get_file_path(shareable_file),
                           DROPBOX_TARGET, dropbox_client)
    frappe.db.close()
    # print "after upload"
    # print("envelop_name = {}".format(envelop_name))
    # print("shareable_file_name = {}".format(shareable_file_name))

    return "uploaded"


def get_html_data(doctype, name):
    """Document -> HTML."""
    html = frappe.get_print(doctype, name)
    return html


def save_generated_file(content, to_name):
    from frappe.utils.file_manager import save_file_on_filesystem
    file_name = "{}.html".format(to_name.replace(" ", "-").replace("/", "-"))
    # print " to_name = {} ".format(to_name)
    save_file_on_filesystem(file_name, content, None, is_private=0)
    return file_name


def get_file_path(file_name):
    return '{}/{}'.format(frappe.get_site_path("public", "files"), file_name)
