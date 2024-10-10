import random
import math

def objective1(vector):
    water, sunlight, nutrients = vector
    return (0.8 * water) + (1.2 * sunlight) + (1.5 * nutrients)

def objective2(vector):
    water, sunlight, nutrients = vector
    return ((water - 50.0) ** 2.0) + ((sunlight - 6.0) ** 2.0) + ((nutrients - 25.0) ** 2.0)

def decode(bitstring, search_space, bits_per_param):
    vector = []
    for i, bounds in enumerate(search_space):
        off, sum_ = i * bits_per_param, 0.0
        param = bitstring[off:(off + bits_per_param)][::-1]
        for j in range(len(param)):
            sum_ += (1.0 if param[j] == '1' else 0.0) * (2.0 ** float(j))
        min_, max_ = bounds
        vector.append(min_ + ((max_ - min_) / ((2.0 ** bits_per_param) - 1.0)) * sum_)
    return vector

def point_mutation(bitstring, rate=1.0 / 1):
    rate = 1.0 / len(bitstring) if rate is None else rate
    child = ''
    for bit in bitstring:
        child += '0' if random.random() < rate and bit == '1' else '1' if random.random() < rate else bit
    return child

def binary_tournament(pop):
    i, j = random.randint(0, len(pop) - 1), random.randint(0, len(pop) - 1)
    while j == i:
        j = random.randint(0, len(pop) - 1)
    return pop[i] if pop[i]['fitness'] < pop[j]['fitness'] else pop[j]

def crossover(parent1, parent2, rate):
    if random.random() >= rate:
        return parent1
    child = ''
    for p1, p2 in zip(parent1, parent2):
        child += p1 if random.random() < 0.5 else p2
    return child

def reproduce(selected, pop_size, p_cross):
    children = []
    for i, p1 in enumerate(selected):
        p2 = selected[i + 1] if i % 2 == 0 else selected[i - 1]
        if i == len(selected) - 1:
            p2 = selected[0]
        child = {}
        child['bitstring'] = crossover(p1['bitstring'], p2['bitstring'], p_cross)
        child['bitstring'] = point_mutation(child['bitstring'])
        children.append(child)
        if len(children) >= pop_size:
            break
    return children

def random_bitstring(num_bits):
    return ''.join('1' if random.random() < 0.5 else '0' for _ in range(num_bits))

def calculate_objectives(pop, search_space, bits_per_param):
    for p in pop:
        p['vector'] = decode(p['bitstring'], search_space, bits_per_param)
        p['objectives'] = [objective1(p['vector']), objective2(p['vector'])]

def dominates(p1, p2):
    for i in range(len(p1['objectives'])):
        if p1['objectives'][i] > p2['objectives'][i]:
            return False
    return True

def weighted_sum(x):
    return sum(x['objectives'])

def euclidean_distance(c1, c2):
    return math.sqrt(sum((c1[i] - c2[i]) ** 2.0 for i in range(len(c1))))

def calculate_dominated(pop):
    for p1 in pop:
        p1['dom_set'] = [p2 for p2 in pop if p1 != p2 and dominates(p1, p2)]

def calculate_raw_fitness(p1, pop):
    return sum(len(p2['dom_set']) for p2 in pop if dominates(p2, p1))

def calculate_density(p1, pop):
    for p2 in pop:
        p2['dist'] = euclidean_distance(p1['objectives'], p2['objectives'])
    sorted_pop = sorted(pop, key=lambda x: x['dist'])
    k = int(math.sqrt(len(pop)))
    return 1.0 / (sorted_pop[k]['dist'] + 2.0)

def calculate_fitness(pop, archive, search_space, bits_per_param):
    calculate_objectives(pop, search_space, bits_per_param)
    union = archive + pop
    calculate_dominated(union)
    for p in union:
        p['raw_fitness'] = calculate_raw_fitness(p, union)
        p['density'] = calculate_density(p, union)
        p['fitness'] = p['raw_fitness'] + p['density']

def environmental_selection(pop, archive, archive_size):
    union = archive + pop
    environment = [p for p in union if p['fitness'] < 1.0]
    if len(environment) < archive_size:
        union.sort(key=lambda p: p['fitness'])
        for p in union:
            if p['fitness'] >= 1.0:
                environment.append(p)
            if len(environment) >= archive_size:
                break
    elif len(environment) > archive_size:
        while len(environment) > archive_size:
            for p1 in environment:
                for p2 in environment:
                    p2['dist'] = euclidean_distance(p1['objectives'], p2['objectives'])
            environment.sort(key=lambda x: x['density'])
            environment.pop(0)
    return environment

def search(search_space, max_gens, pop_size, archive_size, p_cross, bits_per_param=16):
    pop = [{'bitstring': random_bitstring(len(search_space) * bits_per_param)} for _ in range(pop_size)]
    gen, archive = 0, []

    while True:
        calculate_fitness(pop, archive, search_space, bits_per_param)
        archive = environmental_selection(pop, archive, archive_size)
        best = sorted(archive, key=lambda x: weighted_sum(x))[0]
        print(f">gen={gen}, plant_size={best['objectives'][0]}, resource_penalty={best['objectives'][1]}")
        if gen >= max_gens:
            break
        selected = [binary_tournament(archive) for _ in range(pop_size)]
        pop = reproduce(selected, pop_size, p_cross)
        gen += 1

    return archive

if __name__ == '__main__':
    problem_size = 3
    search_space = [[0, 100], [0, 12], [0, 50]]

    max_gens = 50
    pop_size = 80
    archive_size = 40
    p_cross = 0.90

    pop = search(search_space, max_gens, pop_size, archive_size, p_cross)
