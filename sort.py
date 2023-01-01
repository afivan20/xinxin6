def quickort(array): 
    if len(array) < 2:
        return array
    else:
        pivot = array[0]
        less = [i for i in array[1:] if i['start'] < pivot['start']]
        greater = [i for i in array[1:] if i['start'] >= pivot['start']]
        return quickort(less) + [pivot] + quickort(greater)
