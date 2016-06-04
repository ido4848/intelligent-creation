# -*- coding: utf-8 -*-
import sys
import pydub
import fnmatch
import os
import shelve


class Music_DB:
    def __init__(self, db_name, predicate):
        self._name = db_name
        db = shelve.open(self._name)
        db.close()
        self._db_instance = None

    def __enter__(self):
        if self._db_instance is None:
            self._db_instance = shelve.open(self._name)

    def __exit__(self, type, value, traceback):
        if self._db_instance is not None:
            self._db_instance.close()
            self._db_instance = None

    def _open_song(self, song_file, file_format):
        raise NotImplementedError()

    def add_song(self, song_name, song_file, file_format):
        if self._db_instance is None:
            raise Exception("Db is not open!")

        if song_name in self._db_instance:
            raise Exception("Song name already in db!")

        self._db_instance[song_name] = self._open_song(song_file, file_format)

    def remove_song(self, song_name):
        if self._db_instance is None:
            raise Exception("Db is not open!")

        if song_name not in self._db_instance:
            raise Exception("Song name is not in db!")

        del self._db_instance[song_name]

    def get_song(self, song_name):
        if self._db_instance is None:
            raise Exception("Db is not open!")

        if song_name not in self._db_instance:
            raise Exception("Song name is not in db!")

        return self._db_instance[song_name]




def does_song_match(song, frame_rate, channels):
    return song.frame_rate == frame_rate and song.channels == channels


def split_song(song, duration_in_seconds):
    offset = 0
    duration = duration_in_seconds * 1000
    song_segments = []
    while offset + duration < song.duration_seconds * 1000:
        song_segments.append(song[offset:offset + duration])
        offset = offset + duration
    if duration < song.duration_seconds:
        song_segments.append(song[-duration])

    return song_segments


def collect_file_paths(folder, file_extension_regex):
    file_paths = []
    for root, _, file_names in os.walk(folder):
        for file_name in fnmatch.filter(file_names,'*.' + file_extension_regex):
            file_paths.append(root + "/" + file_name)
    return file_paths


def get_mp3_songs(file_paths):
    songs = []
    for file_path in file_paths:
        try:
            songs.append(pydub.AudioSegment.from_mp3(file_path))
        except:
            print "Error getting file {}".format(file_path)
            continue
    return songs


def get_wav_songs(file_paths):
    songs = []
    for file_path in file_paths:
        try:
            songs.append(pydub.AudioSegment.from_wav(file_path))
        except:
            print "Error getting file {}".format(file_path)
            continue
    return songs


def collect_mp3_songs(folder):
    return get_mp3_songs(collect_file_paths(folder, "[Mm][Pp]3"))


def collect_wav_songs(folder):
    return get_wav_songs(collect_file_paths(folder, "[Ww][Aa][Vv]"))


def store_music_db(db_name, songs):
    if not os.path.exists(db_name):
        os.makedirs(db_name)

    joblib.dump(songs, db_name + "/dbfile.pkl", compress=5)


def main():
    FRAME_RATE = 44100
    CHANNELS = 2

    if len(sys.argv) != 4:
        print "Bad usage! usage is {} " \
            "<music-folder-path> <duration_in_seconds>" \
            " <music-db-name>".format(sys.argv[0])
        return

    music_folder = sys.argv[1]
    duration_in_seconds = int(sys.argv[2])
    db_name = sys.argv[3]

    songs = []
    songs += collect_mp3_songs(music_folder)
    songs += collect_wav_songs(music_folder)

    song_segments = []

    for song in songs:
        if not does_song_match(song, FRAME_RATE, CHANNELS):
            continue
        try:
            song_segments += split_song(song, duration_in_seconds)
        except:
            print "Error in spliting song {}".format(song)

    print "There were {} suitable song segments".format(len(song_segments))

    store_music_db(db_name, song_segments)

if __name__ == "__main__":
    main()