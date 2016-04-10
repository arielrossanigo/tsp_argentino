import math
import random
from collections import namedtuple
from functools import lru_cache

City = namedtuple('City', 'id,name,x,y')


@lru_cache()
def distance(id1, id2):
    '''Return the euclidean distance between two cities'''
    if (id1, id2) in PIQUETES:
        return 1e12

    c1 = CITIES[id1]
    c2 = CITIES[id2]
    return math.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2)


def is_neighbor(city, other_city):
    return city != other_city and (city, other_city) not in PIQUETES


def neighbors(city, not_visited):
    return [x for x in not_visited if is_neighbor(city, x)]


def compute_probabilities(city, not_visited, pheromone, alpha=1, beta=1):
    N = neighbors(city, not_visited)
    total = sum([pheromone[(city, destiny)] ** alpha * (1/distance(city, destiny)) ** beta
                 for destiny in N])
    result = [
        (destiny, (pheromone[(city, destiny)] ** alpha * (1/distance(city, destiny)) ** beta)/total)
        for destiny in N
    ]
    return result


def choose_with_probabilities(current_city, not_visited, pheromone):
    r = random.random()
    accum_prob = 0
    for city, prob in compute_probabilities(current_city, not_visited, pheromone):
        assert is_neighbor(current_city, city)
        accum_prob += prob
        if r <= accum_prob:
            return city


def path_cost(path):
    return sum(distance(c1, c2) for c1, c2 in zip(path[:-1], path[1:]))


class Ant:
    def __init__(self, cities):
        self.last_tour = []
        self.last_cost = 0
        self.cities = cities

    def make_tour(self, pheromone, initial_city=None):
        not_visited = self.cities[:]
        if initial_city is None:
            initial_city = random.choice(not_visited)
        else:
            initial_city = initial_city

        current_city = initial_city
        not_visited.remove(current_city)
        self.last_tour = [current_city]

        dead = False
        while not_visited and not dead:
            try:
                next_city = choose_with_probabilities(current_city, not_visited, pheromone)
                self.last_tour.append(next_city)
                not_visited.remove(next_city)
                current_city = next_city
            except:
                dead = True
        if dead:
            self.last_tour = []
        else:
            if not is_neighbor(self.last_tour[-1], initial_city):
                self.last_tour = []
            else:
                self.last_tour.append(initial_city)
                self.last_cost = path_cost(self.last_tour)


def two_opt(current_path, current_cost):
    changes = True
    i = 0
    while changes and i < 10:
        i += 1
        changes = False
        for i in range(1, len(current_path)-2):
            for j in range(i+1, len(current_path)-1):
                o = current_path[:]
                o[i], o[j] = o[j], o[i]
                c = path_cost(o)
                if c < current_cost:
                    current_cost = c
                    current_path = o
                    changes = True
    return current_path, current_cost


def aco(cities):
    # initialize parameters
    current_pheromones = {(x, y): 1 for x in cities for y in cities if x != y}
    ants = [Ant(cities) for x in range(200)]

    iterations = []
    avg_costs = []

    iteration = 0
    stagnation = False
    while (iteration < 200 and not stagnation):
        # every ant makes his solution
        for a in ants:
            a.make_tour(current_pheromones)

        # update pheromone trails
        minimal_path_cost = 10e10
        delta_pheromones = {k: 0 for k in current_pheromones.keys()}

        total_cost = 0.0
        ants_no_dead = [x for x in ants if len(x.last_tour) > 0]
        selected_ants = sorted(ants_no_dead, key=lambda x: x.last_cost)[:10]
        for a in selected_ants:
            a.last_tour, a.last_cost = two_opt(a.last_tour, a.last_cost)
            L = a.last_cost
            total_cost += L
            if L < minimal_path_cost:
                minimal_path_cost = L
            for c1, c2 in zip(a.last_tour[:-1], a.last_tour[1:]):
                delta_pheromones[(c1, c2)] += 1/L

        for k, delta in delta_pheromones.items():
            current_pheromones[k] = (0.8) * current_pheromones[k] + delta / len(selected_ants)

        iterations.append(iteration)
        avg_costs.append(total_cost / len(selected_ants))

        if iteration % 5 == 0:
            print('Iteration: {:>5} ## Minimal tour: {:.2f} ## AVG: {:.2f}'.format(
                iteration, minimal_path_cost, avg_costs[-1])
            )

        stagnation = len(avg_costs) > 20 and all(avg_costs[-1] == x for x in avg_costs[-10:])
        if stagnation:
            print('stagnation!')
        iteration += 1

    ant = ants[0]
    ant.make_tour(current_pheromones, initial_city=0)
    current_path = ant.last_tour
    current_cost = ant.last_cost
    current_path, current_cost = two_opt(current_path, current_cost)
    return current_path, current_cost

if __name__ == '__main__':
    CITIES = []
    for id_, line in enumerate(open('coordenadas.txt').readlines()):
        x, y, name = line.strip().split(',')
        x = float(x)
        y = float(y)
        CITIES.append(City(id_, name, x, y))

    PIQUETES = [(6, 15), (13, 3), (11, 18), (1, 7), (9, 16)]
    PIQUETES.extend([(y, x) for x, y in PIQUETES])  # piquetes affects in both ways

    path, cost = aco([x.id for x in CITIES[:]])
    print("Path: {} ## Cost: {}".format(path, cost))
