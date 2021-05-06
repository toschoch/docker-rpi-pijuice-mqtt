def GetChargeLevel():
    return {'data': 42, 'error': 'NO_ERROR'}


def GetBatteryTemperature():
    return {'data': 25.4, 'error': 'NO_ERROR'}


def GetBatteryVoltage():
    return {'data': 3111, 'error': 'NO_ERROR'}


def GetBatteryCurrent():
    return {'data': 800, 'error': 'NO_ERROR'}


def GetIoVoltage():
    return {'data': 5432, 'error': 'NO_ERROR'}


def GetIoCurrent():
    return {'data': 300, 'error': 'NO_ERROR'}


def GetStatus():
    return {'data': {
        'powerInput': 'adapter connected',
        'powerInput5vIo': 'powered'
    }, 'error': 'NO_ERROR'}
