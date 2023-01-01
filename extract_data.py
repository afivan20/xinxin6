from datetime import datetime
import time 

def extract_data_lingoace(data):
    result = []
    for lesson in data['tutorTimetableList']:
        start_utc = lesson['startTime']
        end_utc = lesson['endTime']
        dt_start = datetime.strptime(start_utc, '%Y-%m-%dT%H:%M:00.000Z')
        dt_end = datetime.strptime(end_utc, '%Y-%m-%dT%H:%M:00.000Z')
        unix_start = int(time.mktime(dt_start.timetuple()) + 10800) # +3 hours 
        unix_end = int(time.mktime(dt_end.timetuple()) + 10800) # +3 hours 
        name = lesson['studentUsername']
        data = {'start':unix_start, 'end':unix_end, 'name': name}
        result.append(data)
    return result


def extract_data_qkid(data):
    result = []
    # что если data пришли False, как отличить от пустого списка? []
    for lesson in data:
         if lesson['status'] == 0:
            start = lesson['beginAt']
            end = lesson['endAt']
            level = lesson['params'].get('abbreviation')
            unit = lesson['params'].get('lessonName')
            if level:
                name = f'{level} - {unit}'
            else:
                name = 'Reading class'
            result.append({'start':start, 'end':end, 'name': name})
    return result
