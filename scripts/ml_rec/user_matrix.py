import numpy as np

def sub_distance(arr1, arr2):
    arr1n = np.asarray(arr1)
    arr2n = np.asarray(arr2)
    if np.argmax(arr1n) == np.argmax(arr2n):
        return 0.0
    else:
        return 2**0.5


def euclidean_distance(arr1, arr2):
    arr1n = np.asarray(arr1)
    arr2n = np.asarray(arr2)
    arr3n = (arr2n - arr1n)**2
    return np.sum(arr3n)**0.5


def user_matrix_distance(u1, u2):
    drive_distance = ((u1['drive'] - u2['drive'])**2)**0.5
    enrollment_distance = ((u1['enrollment'] - u2['enrollment'])**2)**0.5
    year_distance = sub_distance(u1['year'], u2['year'])
    house_distance = euclidean_distance(u1['housing'], u2['housing'])
    school_distance = sub_distance(u1['school'], u2['school'])
    categories_distance = euclidean_distance(u1['categories'], u2['categories'])
    return (0.125*drive_distance) + (0.075*enrollment_distance) + (0.25*house_distance) + (0.15*year_distance) + (0.125*school_distance) + (0.275*categories_distance)
