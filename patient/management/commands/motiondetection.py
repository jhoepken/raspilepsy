from django.core.management import BaseCommand

class Command(BaseCommand):

    help = """
    Server application for raspilepsy that takes care of continuous video
    surveillance, seizure/motion detection and video recording. Videos of
    seizures get stored automatically in database that is accessible via a
    Django webapp.  This server application serves only for the purpose of data
    aquisition and should be run via a cronjob. The users will not interact with
    it.
    """
    
    def handle(self, *args, **options):

        self.stdout.write("FOOBAR")
