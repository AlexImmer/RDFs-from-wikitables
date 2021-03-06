﻿import os.path
from _thread import start_new_thread, allocate_lock
from collections import defaultdict
from django.core.management.base import BaseCommand
from RDFs.models import RDF, Page
from RDFsFromWikitables.settings import PROJECT_DIR
from wikitables.page import Page as wikipage
import wikipedia

THREAD_MAX = 16

num_threads = 0
lock = allocate_lock()
db_lock = allocate_lock()

class Command(BaseCommand):
    def handle(self, *args, **options):
        runner = 0
        try:
            global num_threads, lock, db_lock
            titlesFile = os.path.join(PROJECT_DIR, "data/Titles.txt")
            print(titlesFile)
            with open(titlesFile) as f:
                content = f.readlines()
            print(str(len(content)) + ' lines in file')
            try:
                for line in content:
                    runner += 1
                    print(str(runner) + ' current line')
                    while(True):
                        lock.acquire()
                        if num_threads < THREAD_MAX:
                            break
                        lock.release()

                    db_lock.acquire()
                    if not Page.objects.filter(title=str(line)):
                        db_lock.release()
                        num_threads += 1
                        start_new_thread(generateRDFsFor,(line,))
                    else:
                        db_lock.release()
                    lock.release()

            except Exception as inst:
                print("Error appeared: " + str(type(inst)))
                print(inst.args)
                print("Failure")
        except Exception as inst:
            print("Couldn´t open file in given directory")

def generateRDFsFor(title):
    global num_threads, lock, db_lock, averageCrawl, countCrawl, averageExtr, countExtr, averageDb, countDb

    print("Title: "+ str(title).strip())

    try:
        wpage = None
        try:

            wpage = wikipage(title)

        except:
            print("\n------------------------------\n" +
                    "Couldn\'t find wikipedia page with this title\n" +
                    "FAILED for page with title: " + str(title).strip() + "\n" +
                    "------------------------------")

        acquired = False
        db_lock.acquire()
        if wpage and not Page.objects.filter(link=(str(wpage.url))):
            db_lock.release()
            pg = Page(title=str(title), link=str(wpage.url), html=wpage.html)
            pg.save()
            if wpage.hasTable:
                i = 0
                for table in wpage.tables:
                    i += 1

                    tb = Table(page=pg, table_number=i, number_of_tablerows=len(table.rows))
                    tb.save()

                    rdfs = table.generateRDFs()

                    print(str(len(rdfs)) + ' new RDFs generated for table ' + str(title).strip())
                    for rdf in rdfs:
                        # save the data:
                        db_lock.acquire()
                        acquired = True
                        # exclude errors like empty subject, predicate or object and
                        # errors such as subject != resource
                        if rdf[0] and rdf[1] and rdf[2] and ('/resource/' in rdf[0]):
                            RDF(table=tb, rdf_subject=rdf[0], rdf_predicate=rdf[1], rdf_object=rdf[2],
                                    object_column_name=rdf[3], relative_occurency=rdf[4],
                                    subject_is_tablekey=rdf[5], object_is_tablekey=rdf[6]).save()
                        db_lock.release()
                        acquired = False
            else:
                print('Page with title \''+str(title).strip()+'\' has no tables')
        else:
            db_lock.release()
            print('Page with title \'' + str(title).strip() + '\' has been extracted already')
    except Exception as inst:
        print("\n------------------------------\n" +
                "Error appeared: " + str(type(inst)) + "\n" +
                str(inst.args) + "\n" +
                "FAILED for page with title: " + str(title).strip() + "\n" +
                "------------------------------")
    except:
        print("\n------------------------------\n" +
                "Unknown error appeared for page with title: " + str(title).strip() + "\n" +
                "------------------------------")

    if acquired:
        db_lock.release()

    lock.acquire()
    num_threads -= 1
    lock.release()
    return
