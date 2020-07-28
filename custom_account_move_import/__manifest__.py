{
    'name': 'Custom Account Move Import',
    'summary': 'Import Accounting Entries',
    'author': "SIT & think digital",
    'website': "http://sitco.odoo.com/",
    'category': 'Custom',
    'version': '12.0.0.1.3',

    'depends': ['sale_management','account_accountant','analytic',
                ],

    'data': [
        'security/ir.model.access.csv',
        'wizard/import_move_wizard.xml',
        'wizard/import_vendor_bill_wizard.xml',
        'views/res_company_view.xml',
        'views/account_view.xml',
        'views/res_partner_view.xml',
        'views/analytic_tag_view.xml'
    ],

    'demo': [],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
