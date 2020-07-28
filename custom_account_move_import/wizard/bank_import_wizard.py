import tempfile
import base64
import logging
from xlrd import open_workbook
from odoo import api, fields, models, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class CustomAccountMove(models.TransientModel):
    _name = 'custom.bank.import'
    _description = 'Bank Import'

    entry_date = fields.Date("Entry Date", required=True)
    journal_id = fields.Many2one('account.journal', string="Journal", required=True)
    debit_account_id = fields.Many2one('account.account', string='Debit Account',
                                       domain="[('deprecated', '=', False)]", copy=False, required=True)
    expense_account_id = fields.Many2one('account.account', string='Account Expenses',
                                         domain="[('deprecated', '=', False)]", copy=False, required=True)
    expense_credit_id = fields.Many2one('account.account', string='Credit Account',
                                        domain="[('deprecated', '=', False)]", copy=False, required=True)
    purchase_tax_id = fields.Many2one('account.tax', string='Purchase Tax',
                                      domain="[('type_tax_use', '=', 'purchase'),('price_include', '=', False)]",
                                      copy=False, required=True)
    import_file_ids = fields.One2many('custom.account.move.import.files',
                                      'import_bank_id', string='Select Files')

    @api.multi
    def import_bank_data(self):
        acc_move_obj = self.env['account.move']
        move_ids = []
        for each_import_file in self.import_file_ids:
            datafile = each_import_file.csv_file
            file_name = str(each_import_file.filename)
            if not datafile or not \
                    file_name.lower().endswith(('.xlsx')):
                raise Warning(_("Please Select .xlsx file to Import"))
            file_data = base64.decodestring(datafile)
            # move_lines = []
            temp_path = tempfile.gettempdir()
            fp = open(temp_path + '/xsl_file.xls', 'wb+')
            fp.write(file_data)
            fp.close()
            wb = open_workbook(temp_path + '/xsl_file.xls')
            for sheet in wb.sheets():
                for rownum in range(1, sheet.nrows):
                    move_lines = []
                    analytic_tag_rec = False
                    analytic_account_rec = False

                    bank_line = sheet.row_values(rownum)
                    credit = bank_line[5] and float(bank_line[5]) or 0
                    debit = bank_line[6] and abs(float(bank_line[6])) or 0
                    bank_date = bank_line[4]
                    bank_label = bank_line[3]
                    ip_machine = bank_line[2] and bank_line[2].strip() or False
                    sheet_analytic_tag = bank_line[1] and bank_line[1].strip() or False

                    # Get the Analytic TAG
                    if sheet_analytic_tag:
                        analytic_tag_rec = self.env['account.analytic.tag'].search([
                            '|', ('name', '=', sheet_analytic_tag),
                            ('alternate_names_ids.name', '=', sheet_analytic_tag)], limit=1)

                        if not analytic_tag_rec:
                            raise Warning("No Analytic Account TAG with Name: %s" % sheet_analytic_tag)
                        if not analytic_tag_rec.credit_account_id:
                            raise Warning("No Credit Account defined in Tag: %s" % analytic_tag_rec.name)

                    # Get the Analytic Account
                    if ip_machine:
                        analytic_account_rec = self.env['account.analytic.account'].search([
                            ('ip_machines_ids.name', '=', ip_machine)], limit=1)

                        if not analytic_account_rec:
                            raise Warning("No Analytic Account with IP Machine: %s" % ip_machine)

                    if credit and analytic_tag_rec:
                        print ('debit', debit)
                        acc_move_rec = acc_move_obj.create({
                            'journal_id': self.journal_id.id,
                            'date': self.entry_date,
                            'ref': "Bank Entries Imported from " + file_name,
                        })
                        move_ids.append(acc_move_rec.id)
                        debit_move_line_vals = {
                           'analytic_account_id': analytic_account_rec and analytic_account_rec.id or False,
                           'account_id': self.debit_account_id.id,
                           'debit': credit,
                           'name': bank_label,
                           'analytic_tag_ids': analytic_tag_rec and [(6, 0, [analytic_tag_rec.id])] or False,
                           'partner_id': analytic_tag_rec and analytic_tag_rec.partner_id.id or False,
                       }
                        move_lines.append((0, 0, debit_move_line_vals))
                        credit_move_line_vals = {
                            'account_id': analytic_tag_rec and analytic_tag_rec.credit_account_id.id or False,
                            'credit': credit,
                            'name': bank_label,
                            'analytic_account_id': analytic_account_rec and analytic_account_rec.id or False,
                            'analytic_tag_ids': analytic_tag_rec and [(6, 0, [analytic_tag_rec.id])] or False
                        }
                        move_lines.append((0, 0, credit_move_line_vals))
                        acc_move_rec.write({"line_ids": move_lines})

                    if debit and ip_machine \
                        and ip_machine in bank_label \
                            and 'VAT' not in bank_label:
                        acc_move_rec = acc_move_obj.create({
                            'journal_id': self.journal_id.id,
                            'date': self.entry_date,
                            'ref': "Bank Entries Imported from " + file_name,

                        })
                        move_ids.append(acc_move_rec.id)
                        debit_move_line_vals = {
                            'account_id': self.expense_account_id.id,
                            'debit': debit,
                            'name': bank_label,
                            'tax_ids': [(6, 0, [self.purchase_tax_id.id])],
                        }
                        move_lines.append((0, 0, debit_move_line_vals))
                        credit_move_line_vals = {
                            'account_id': self.expense_credit_id.id,
                            'credit': debit,
                            'name': bank_label,
                        }
                        move_lines.append((0, 0, credit_move_line_vals))

                        # Get VAT Amount
                        taxes_vals = self.purchase_tax_id.compute_all(debit)
                        tax_amount = taxes_vals['taxes'][0]['amount']
                        tax_name = taxes_vals['taxes'][0]['name']

                        debit_tax_line_vals = {
                            'account_id': self.purchase_tax_id.account_id.id,
                            'debit': tax_amount,
                            'name': tax_name,
                            'tax_line_id': self.purchase_tax_id.id,
                        }
                        move_lines.append((0, 0, debit_tax_line_vals))
                        credit_tax_line_vals = {
                            'account_id': self.expense_credit_id.id,
                            'credit': tax_amount,
                            'name': tax_name,
                        }
                        move_lines.append((0, 0, credit_tax_line_vals))

                        acc_move_rec.write({"line_ids": move_lines})

        if move_ids:
            return self.action_view_account_move(move_ids)

    @api.multi
    def action_view_account_move(self, move_ids):
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        result['context'] = {}
        result['domain'] = "[('id','in',%s)]" % (move_ids)
        return result
