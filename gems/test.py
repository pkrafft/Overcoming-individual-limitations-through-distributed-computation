
import random
import words


def f(true_prob, false_prob):
    
    classes = random.sample(words.words, 8)

    n_turns = 20
    n_classes = len(classes)
    n_evidence = 4

    true_class = random.choice(classes);

    tests = []
    for t in range(n_turns):
        tests += [[]]
        for i in range(n_evidence):
            tests[t] += [[]]
            for c in classes:
                if c == true_class:
                    prob = true_prob
                else:
                    prob = false_prob
                if random.random() < prob:
                    tests[t][i] += [c]

    return true_class, tests
