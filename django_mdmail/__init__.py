__version__ = '0.5.1'

import os
import sys

from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
if sys.version_info[0] == 3:
    from email.mime.image import MIMEImage
else:
    from email.MIMEImage import MIMEImage
from mdmail import EmailContent


# Warning to be placed in generated text and HTML files.
OVERRIDE_WARNING = 'WARNING! THIS FILE IS AUTO-GENERATED by django_mdmail upon Django startup. Changes to this file WILL be overwritten. In the same directory, there should be a file with the same name, except an ".md" ending (for Markdown). Edit that instead and restart Django.'


def send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None, css=None, attachments=[]):

    # Have `mdmail` do its Markdown magic.
    content = EmailContent(message, css=css)

    # Create the email message and fill it with the relevant data.
    email = EmailMultiAlternatives(
        subject,
        content.text,
        from_email,
        recipient_list
    )
    email.attach_alternative(html_message or content.html, 'text/html')
    email.mixed_subtype = 'related'

    for filename, data in content.inline_images:
        # Create the image from the image data.
        image = MIMEImage(data.read())

        # Give the image an ID so that it can be found via HTML.
        image.add_header('Content-ID', '<{}>'.format(filename))

        # This header allows users of some email clients (for example
        # Thunderbird) to view the images as attachments when displaying the
        # message as plaintext, without it interrupting those users who view
        # it as HTML.
        image.add_header(
            'Content-Disposition', 'attachment; filename=%s' % filename
        )

        # Attach the image.
        email.attach(image)

    for attachment in attachments:
        email.attach(filename=attachment[0], content=attachment[1], mimetype=attachment[2])

    # Finally, send the message.
    email.send(fail_silently)


def convert_md_templates(css=None):
    '''
    Scans template directories for .md files and generates text and
    email-client-friendly HTML files from them, intended for email use.

    Use with AppConfig.ready() hooks (see Django documentation) to run at
    Django startup.

    Example `core/apps.py` file:

        from django.apps import AppConfig

        from django_mdmail import convert_md_templates

        class CoreConfig(AppConfig):
            name = 'core'

            def ready(self):
                convert_md_templates()
    '''

    override_comment = '{%% comment %%}%s{%% endcomment %%}\n' % OVERRIDE_WARNING

    # Add template directories for apps belonging to the running project.
    template_dirs = []
    for app_config in apps.get_app_configs():
        # Check if this app belongs to our project and add its template
        # directory if so.
        if app_config.path == '%s/%s' % (settings.BASE_DIR, app_config.name):
            template_dirs += ['%s/templates' % app_config.path]

    # Iterate the template directories.
    for template_dir in template_dirs:
        for root, subdirs, filenames in os.walk(template_dir):
            for filename in filenames:
                if filename[-3:] == '.md':
                    md_path = os.path.join(root, filename)
                    txt_path = '%s.txt' % md_path[:-3]
                    html_path = '%s.html' % md_path[:-3]

                    with open(md_path, 'r') as f:
                        md_content = f.read()
                        f.close()

                    # Generate email-client-friendly HTML.
                    content = EmailContent(md_content, css=css)

                    with open(txt_path, 'w') as f:
                        f.write(override_comment + content.text)
                        f.close()

                    with open(html_path, 'w') as f:
                        f.write(override_comment + content.html)
                        f.close()
