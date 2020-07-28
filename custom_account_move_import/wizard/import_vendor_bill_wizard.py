import os
import tempfile
import base64
import logging
import xlrd
from xlrd import open_workbook

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT


_logger = logging.getLogger(__name__)

class ImportVendorBill(models.TransientModel):

    _name = 'import.vendor.bill'

    _description = 'Import Vendor Bill'

    xls_file = fields.Binary(string='File', required=1)
    filename = fields.Char(string='Filename')
    product_id = fields.Many2one('product.product', string="Product", required=1)
    purchase_journal_id = fields.Many2one('account.journal', string="Purchase Journal", required=1,
                                          domain="[('type', '=', 'purchase')]")
    expense_account_id = fields.Many2one('account.account', string='Bill Line Account', required=1,
                                         domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]")
    payable_account_id = fields.Many2one('account.account', string='Payable Account', required=1,
                                         domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]")
    tax_id = fields.Many2one('account.tax', string="Purchase Tax", required=1,
                             domain="[('type_tax_use', '=', 'purchase')]")

    @api.model
    def default_get(self, fields):
        result = super(ImportVendorBill, self).default_get(fields)
        company = self.env.user.company_id
        result.update({
                        'expense_account_id': company.expense_account_id.id,
                        'payable_account_id': company.payable_account_id.id,
                        'tax_id': company.purchase_tax_id.id,
                        'purchase_journal_id': company.purchase_journal_id.id,
                        'product_id': company.product_id.id,
                      })
        return result


    @api.multi
    def import_vendor_bill(self):
        datafile = self.xls_file
        file_name = str(self.filename)
        if not datafile or not \
                file_name.lower().endswith(('.xls', '.xlsx')):
            raise Warning(_("Please Select .xlsx or .xls file to Import"))
        partner_obj = self.env['res.partner']
        analytic_account_obj = self.env['account.analytic.account']
        account_invoice_obj = self.env['account.invoice']
        expense_account_id = self.expense_account_id.id
        payable_account_id = self.payable_account_id.id
        tax_id =  self.tax_id.id
        purchase_journal_id = self.purchase_journal_id.id
        product_id = self.product_id.id
        file_data = base64.decodestring(datafile)
        invoice_ids = []
        temp_path = tempfile.gettempdir()
        fp = open(temp_path + '/xsl_file.xls', 'wb+')
        fp.write(file_data)
        fp.close()
        wb = open_workbook(temp_path + '/xsl_file.xls')
        for sheet in wb.sheets():

            partner_name = sheet.row_values(4) and sheet.row_values(4)[0] or ''
            partner_id = False
            if partner_name:
                partner_id = partner_obj.search([('supplier', '=', True), ('name', '=', partner_name)], limit=1)
            if not partner_id:
                partner_id = partner_obj.search([('micros_alternative_name', 'ilike', partner_name)], limit=1)
                if not partner_id:
                    raise Warning("No Vendor found with Name: %s" % partner_name)
            for rownum in range(5, sheet.nrows):
                print (sheet.row_values(rownum))
                branch_name = sheet.row_values(rownum) and sheet.row_values(rownum)[0] or ''
                analytic_acc_id = analytic_account_obj.search([('name', '=', branch_name)], limit=1)
                if not analytic_acc_id:
                    raise Warning("No Analytic account found with Name: %s" % branch_name)
                analytic_acc_id = analytic_acc_id.id
                date_invoice =  xlrd.xldate.xldate_as_datetime(sheet.row_values(rownum)[4], wb.datemode)
                date_due =  xlrd.xldate.xldate_as_datetime(sheet.row_values(rownum)[2], wb.datemode)
                # date_invoice = datetime.strptime(rownum[4], "%d/%m/%Y")
                # date_due = datetime.strptime(rownum[2], "%d/%m/%Y")
                vendor_bill_vals = {
                    'partner_id': partner_id.id,
                    'type': 'in_invoice',
                    'payment_term_id': False,
                    'journal_id': purchase_journal_id,
                    'account_id': payable_account_id,
                    'reference': sheet.row_values(rownum)[1],
                    'date_invoice': date_invoice.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_due': date_due.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'x_analytic_branch': analytic_acc_id,
                    'invoice_line_ids': [(0, 0, {
                                        'product_id': product_id,
                                        'name': sheet.row_values(rownum)[1],
                                        'account_id': expense_account_id,
                                        'account_analytic_id': analytic_acc_id,
                                        'quantity': 1,
                                        'price_unit': sheet.row_values(rownum)[5],
                                        'invoice_line_tax_ids': [
                                            (6, 0, [tax_id])],
                                        })],
                    }
                invoice_id = account_invoice_obj.create(vendor_bill_vals).id
                invoice_ids.append(invoice_id)

        try:
            os.unlink(temp_path + '/xsl_file.xls')
        except (OSError, IOError):
            _logger.error('Error when trying to remove file %s' % temp_path + '/xsl_file.xls')

        if invoice_ids:
            return self.action_view_vendor_bills(invoice_ids)


    @api.multi
    def action_view_vendor_bills(self, invoice_ids):
        action = self.env.ref('account.action_vendor_bill_template')
        result = action.read()[0]
        result['context'] = {}
        result['domain'] = "[('id','in',%s)]" % (invoice_ids)
        return result
