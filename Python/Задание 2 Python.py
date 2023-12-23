# Создал класс Solver, при создании объекта которого подается на вход список,
# кто с кем дружит, и информация о количестве друзей у каждого человека
# сохраняется в словарь, где ключ - это id человека, и значение,
# получаемое по этому ключу - число друзей у этого человека.
# С помощью метода get_friends() этого класса получаем данный словарь
# Пример использования скрипта приведен ниже  (на списках из условия задачи)

class Solver:

    def __init__(self, list_of_people: list):
        self.friends_number_dict = {}
        for people_sublist in list_of_people:
            for person in people_sublist:
                if self.friends_number_dict.get(person) is None:
                    self.friends_number_dict[person] = 0
                if len(people_sublist) > 1:
                    self.friends_number_dict[person] += 1

    def get_friends(self):
        return self.friends_number_dict


if __name__ == '__main__':
    a = [[2, 3], [3, 4], [5], [2, 6], [2, 4], [6, 1]]
    b = [[1, 2], [3], [8], [6, 2]]

    processed_list_a = Solver(a)
    processed_list_b = Solver(b)
    print(f'Friends count for list a: {processed_list_a.get_friends()}'
          f'\nFriends count for list b: {processed_list_b.get_friends()}')
