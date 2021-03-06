import frappe
from erpnext.healthcare.doctype.patient.patient import Patient

original_add_as_website_user = Patient.add_as_website_user
def add_as_website_user(self):
    """
    Create a website user for the patient depending upon the settings
    """
    add_patient_as_a_website_user = frappe.db.get_single_value (
        'Healthcare Settings', 'add_patient_as_a_website_user')
    if add_patient_as_a_website_user:
        original_add_as_website_user(self)

# New definitions
Patient.add_as_website_user = add_as_website_user