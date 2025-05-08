from django.core.management.base import BaseCommand
from search.elasticsearch_client import es, create_index

class Command(BaseCommand):
    help = "Index documents into Elasticsearch"

    def handle(self, *args, **kwargs):
        index_name = "documents"
        create_index(index_name)

        with open("core/data/doc_dump.txt", "r", encoding="utf-8") as f:
          for line in f:
              parts = line.strip().split("\t")
              if len(parts) != 4:
                  continue
              doc_id, url, title, abstract = parts

              doc = {
                  "url": url,
                  "title": title,
                  "abstract": abstract
              }

              es.index(index=index_name, id=doc_id, body=doc)
              
        self.stdout.write(self.style.SUCCESS("Indexing completed."))