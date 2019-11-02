from arus.core.stream import Stream
import PySimpleGUI as sg
from datetime import datetime
from arus.core.libs.date import parse_timestamp
import pandas as pd
from arus.core.libs.mhealth_format.data import segment_annotation
import threading


class AnnotatorGUIStream(Stream):
    """Annotator stream to asyncly load real-time annotations from an interactive GUI interface

    This class inherits `Stream` class to load annotations coming in real-time from an interactive GUI.

    Examples:
        1. Loading annotations every 10 seconds asynchronously from an interactive GUI as users select different annotation labels and print out each one instantly.

        ```python
        labels = ['Sitting', "Standing", "Walking", "Jumping", "Climbing", "Lying"]
        stream = AnnotatorGUIStream(labels,
                                    window_size=5, start_time=None)
        stream.start(scheduler='thread')
        for data in stream.get_iterator():
            print(data)
        ```
    """

    def __init__(self, labels, window_size, start_time=None, name='annotator-gui', scheduler='thread'):
        super().__init__(data_source=labels, window_size=window_size,
                         start_time=start_time, name=name, scheduler=scheduler)
        self._start_time = parse_timestamp(
            datetime.now()) if self._start_time is None else self._start_time
        self._annotations = {}

    def _init_annotator_gui(self, labels):
        layout = []
        row_layout = []
        i = 0
        for label in labels:
            i = i + 1
            if i % 5 == 0:
                layout.append(row_layout)
                row_layout = []
            label_button = sg.Button(button_text=label, key="LABEL_" + label,
                                     button_color=("white", "red"), font='Arial', size=(10, 2))
            row_layout.append(label_button)
            self._annotations[label_button.ButtonText] = {
                "START_TIME": [],
                "STOP_TIME": [],
                "Element": label_button
            }
        layout.append(row_layout)
        layout.append([sg.CloseButton('Close')])
        window = sg.Window("Annotator pad").layout(layout)
        while True:
            event, values = window.read()
            if event in (None, 'Close'):   # if user closes window or clicks cancel
                break
            if 'LABEL' in event:
                data = event.replace('LABEL_', '')
                self._update_button(data)
                self._update_annotations(data)

    def _send_data(self, st):
        while True:
            current_time = parse_timestamp(datetime.now())
            if current_time - st >= pd.Timedelta(self._window_size, 's'):
                # format annotatons
                data = {'HEADER_TIME_STAMP': [], 'START_TIME': [],
                        'STOP_TIME': [], 'LABEL_NAME': []}
                for label, times in self._annotations.items():
                    stop_time_list = times['STOP_TIME'].copy()
                    if len(times['START_TIME']) > len(stop_time_list):
                        stop_time_list.append(current_time)
                    for start_time, stop_time in zip(times['START_TIME'], stop_time_list):
                        data['HEADER_TIME_STAMP'].append(start_time)
                        data['START_TIME'].append(start_time)
                        data['STOP_TIME'].append(stop_time)
                        data['LABEL_NAME'].append(label)
                data = pd.DataFrame.from_dict(data, orient='columns')
                data = data.sort_values(by=['START_TIME'])
                if data.empty:
                    st = current_time
                    self._put_data_in_queue('No annotations available')
                    continue
                data = segment_annotation(
                    data, start_time=st, stop_time=current_time)
                if data.empty:
                    self._put_data_in_queue('No annotations available')
                else:
                    self._put_data_in_queue(data)
                st = current_time

    def _update_button(self, label):
        current_color = self._annotations[label]["Element"].ButtonColor
        if current_color[1] == "red":
            self._annotations[label]["Element"].Update(
                button_color=('white', 'green'))
        else:
            self._annotations[label]["Element"].Update(
                button_color=('white', 'red'))

    def _update_annotations(self, label):
        ongoing = len(self._annotations[label]['START_TIME']) > len(
            self._annotations[label]['STOP_TIME'])
        if ongoing:
            self._annotations[label]['STOP_TIME'].append(
                parse_timestamp(datetime.now()))
        else:
            self._annotations[label]['START_TIME'].append(
                parse_timestamp(datetime.now()))

    def load_(self, obj_toload):
        labels = obj_toload
        sender_thread = threading.Thread(
            target=self._send_data, name=self.name+"-sender", args=(self._start_time,))
        sender_thread.start()
        self._init_annotator_gui(labels)
