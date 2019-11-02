

from arus_components_hci.streams import AnnotatorGUIStream


if __name__ == "__main__":
    labels = ['Sitting', "Standing", "Walking", "Jumping", "Climbing", "Lying"]
    stream = AnnotatorGUIStream(labels,
                                window_size=2, start_time=None)
    stream.start(scheduler='thread')
    for data in stream.get_iterator():
        print(data)
