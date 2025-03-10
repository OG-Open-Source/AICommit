from .whatsdifferent import WhatsDifferent, Change, ChangeLocation

def set_format(format_type):
	WhatsDifferent.set_format(format_type)

__all__ = ['WhatsDifferent', 'Change', 'ChangeLocation', 'set_format']