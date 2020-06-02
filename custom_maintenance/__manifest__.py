# -*- coding: utf-8 -*-
{
    'name': "Custom Maintenance",
    'summary': """Customization for maintenance""",
    'author': "SIT & think digital",
    'website': "http://sitco.odoo.com/",
    'category': 'Custom',
    'version': '12.0.1',

    'depends': ['maintenance','repair'],

    'data': [
        'views/model_view.xml',
            ],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
