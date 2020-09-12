from setuptools import setup

setup(
    name='graphicone_google_api',
    url='https://github.com/trendvision/graphicone_google_api',
    packages=['graphicone_google_api'],
    install_requires=['httplib2', 'google-api-python-client', 'oauth2client', 'datetime'],
    version='0.1',
    license='TRV',
    description='Interact with google spreadsheets',
)
