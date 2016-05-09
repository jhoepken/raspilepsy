from django.core.management import BaseCommand

class Command(BaseCommand):

    help = "You are on your own"
    
    def handle(self, *args, **options):

        self.stdout.write("FOOBAR")
