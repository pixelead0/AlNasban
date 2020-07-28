import os
import tempfile
import base64
import logging
import xlrd
from pytz import timezone

from odoo import api, fields, models, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class ImportHrAttendance(models.TransientModel):

    _name = 'import.hr.attendance'

    _description = 'Import HR Attendance'

    xls_file = fields.Binary(string='File', required=1)
    filename = fields.Char(string='Filename')

    @api.multi
    def action_import_attendances(self):
        datafile = self.xls_file
        file_name = str(self.filename)
        if not datafile or not \
                file_name.lower().endswith(('.xls', '.xlsx')):
            raise Warning(_("Please Select .xlsx or .xls file to Import"))
        employee_obj = self.env['hr.employee']
        attendance_obj = self.env['hr.attendance']
        file_data = base64.decodestring(datafile)
        attendances = []
        utc_tz = timezone('UTC')
        user_tz = timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        identification_id = False
        temp_path = tempfile.gettempdir()
        fp = open(temp_path + '/xsl_file.xls', 'wb+')
        fp.write(file_data)
        fp.close()
        wb = xlrd.open_workbook(temp_path + '/xsl_file.xls')
        for sheet in wb.sheets():
            for rownum in range(5, sheet.nrows):
                if sheet.row_values(rownum)[9] != 0.0 and sheet.row_values(rownum)[1]:
                    identification_id = sheet.row_values(rownum)[1]
                    employee_id = employee_obj.search([('identification_id', '=', identification_id)], limit=1)
                    if not employee_id:
                        raise Warning("No Employee found with Identification No: %s" % identification_id)
                    employee_id = employee_id.id
                elif identification_id and sheet.row_values(rownum)[1] and sheet.row_values(rownum)[2]:
                    raw_check_in = xlrd.xldate.xldate_as_datetime(sheet.row_values(rownum)[1], wb.datemode)
                    localized_dt = user_tz.localize(raw_check_in)
                    check_in = localized_dt.astimezone(utc_tz).replace(tzinfo=None)
                    raw_check_out = xlrd.xldate.xldate_as_datetime(sheet.row_values(rownum)[2], wb.datemode)
                    localized_dt = user_tz.localize(raw_check_out)
                    check_out = localized_dt.astimezone(utc_tz).replace(tzinfo=None)
                    attendance_vals = {
                                    'employee_id': employee_id,
                                    'check_in': check_in,
                                    'check_out': check_out}
                    attendance_id = attendance_obj.create(attendance_vals)
                    attendances.append(attendance_id.id)
        try:
            os.unlink(temp_path + '/xsl_file.xls')
        except (OSError, IOError):
            _logger.error('Error when trying to remove file %s' % temp_path + '/xsl_file.xls')

        if attendances:
            return self.action_view_attendances(attendances)

    @api.multi
    def action_view_attendances(self, attendances):
        action = self.env.ref('hr_attendance.hr_attendance_action')
        result = action.read()[0]
        result['context'] = {}
        result['domain'] = "[('id','in',%s)]" % (attendances)
        return result
