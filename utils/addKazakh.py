import csv
from collections import defaultdict

import numpy

sz_user = 610
sz_movie = 193609


def fill_rating():
    csv_path_from = "/Users/aida/Downloads/kazakh.csv"
    csv_path_to = "/Users/aida/Downloads/cinema/DiplomaProject/api/views/ratings.csv"
    columns = defaultdict(list)
    with open(csv_path_from, "r") as f_obj:
        csv_reader = csv.DictReader(f_obj)
        for row in csv_reader:  # read a row as {column1: value1, column2: value2,...}
            for (k, v) in row.items():  # go over each column name and value
                columns[k].append(v)
    with open(csv_path_to, mode='a') as csv_file:
        for movie in range(1, 12):
            fieldnames = ['userId', 'movieId', 'rating', 'timestamp']
            # print(columns[str(movie)])
            # userId	movieId	rating
            writer = csv.DictWriter(csv_file, fieldnames)
            for user in range(len(columns[str(movie)])):
                if columns[str(movie)][user]:
                    writer.writerow({"userId": str(user + sz_user), "movieId": str(movie + sz_movie),
                                     "rating": str(columns[str(movie)][user]), 'timestamp': str(0)})


def fill_movies():
    # movieId,title,genres
    names = ['The Road to Mother', 'Kanikuly off-line', 'MYN BALA: WARRIORS OF THE STEPPE', 'Kelinka Sabina',
             'Kazakh Business', 'Kudalar', 'Tomiris', 'Biznesmeny', 'Finding Mother', 'Balalyq shaghymyng aspany',
             'My love is Aisulu']
    genres = ['War|Drama', 'Comedy|Family', 'Drama|History', 'Comedy',
              'Comedy', 'Comedy|Family', 'Drama|History', 'Drama',
              'Drama|Comedy', 'Drama|History', 'Comedy|Romance']
    csv_path_to = "/Users/aida/Downloads/cinema/DiplomaProject/api/views/movies.csv"
    with open(csv_path_to, mode='a') as csv_file:
        for movie in range(0, len(names)):
            fieldnames = ['movieId', 'title', 'genres']
            writer = csv.DictWriter(csv_file, fieldnames)
            writer.writerow({"movieId": str(movie + sz_movie + 1), "title": names[movie],
                             'genres': genres[movie]})


