
import math
import itertools

TRANSITIONS = {

2: {

    # n-state transitions
    (0, 0, 0, 0): lambda p_ns,p_i,p_e: p_ns*p_i*(1-p_e),
    (0, 0,-1, 0): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*(1-p_e),
    (0, 0, 0, 1): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*p_e,
    (0, 0,-1, 1): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*p_e,

    # s-state transitions
    (1, 0, 0, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*(1-p_e),
    (1, 0,-1, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*(1-p_e),
    (1, 1, 0, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*(1-p_e),
    (1, 1,-1, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*(1-p_e),
    (1, 0, 0, 1): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*p_e,
    (1, 0,-1, 1): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*p_e,
    (1, 1, 0, 1): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*p_e,
    (1, 1,-1, 1): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*p_e,
},


3: {

    # n-state transitions
    (0,-1, 0, 0): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*(1-p_e),
    (0,-1, 1, 0): lambda p_ns,p_i,p_e: p_ns*p_i*(1-p_e),
    (0,-1, 0, 1): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*p_e,
    (0,-1, 1, 1): lambda p_ns,p_i,p_e: p_ns*p_i*p_e,

    # s-state transitions
    (1, 0, 0, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*(1-p_e),
    (1, 0, 1, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*(1-p_e),
    (1,-1, 0, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*(1-p_e),
    (1,-1, 1, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*(1-p_e),
    (1, 0, 0, 1): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*p_e,
    (1, 0, 1, 1): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*p_e,
    (1,-1, 0, 1): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*p_e,
    (1,-1, 1, 1): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*p_e,
},


1: {

    # n-state transitions
    (0, 0, 0, -1): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*(1-p_e),
    (0, 0, 1, -1): lambda p_ns,p_i,p_e: p_ns*p_i*(1-p_e),
    (0, 0, 0, 0): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*p_e,
    (0, 0, 1, 0): lambda p_ns,p_i,p_e: p_ns*p_i*p_e,

    # s-state transitions
    (1, 0, 0, -1): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*(1-p_e),
    (1, 0, 1, -1): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*(1-p_e),
    (1, 1, 0, -1): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*(1-p_e),
    (1, 1, 1, -1): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*(1-p_e),
    (1, 0, 0, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*p_e,
    (1, 0, 1, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*p_e,
    (1, 1, 0, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*p_e,
    (1, 1, 1, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*p_e,
},
4: {

    # n-state transitions
    (0, 0, 1, 0): lambda p_ns, p_i, p_e: p_ns * p_i * (1 - p_e),
    (0, 0, 0, 0): lambda p_ns, p_i, p_e: p_ns * (1 - p_i) * (1 - p_e),
    (0, 0, 1, 1): lambda p_ns, p_i, p_e: p_ns * p_i * p_e,
    (0, 0, 0, 1): lambda p_ns, p_i, p_e: p_ns * (1 - p_i) * p_e,

    # s-state transitions
    (1, 0, 1, 0): lambda p_ns, p_i, p_e: 0.16 * p_ns * p_i * (1 - p_e),
    (1, 0, 0, 0): lambda p_ns, p_i, p_e: 0.16 * p_ns * (1 - p_i) * (1 - p_e),
    (1, 1, 1, 0): lambda p_ns, p_i, p_e: 0.84 * p_ns * p_i * (1 - p_e),
    (1, 1, 0, 0): lambda p_ns, p_i, p_e: 0.84 * p_ns * (1 - p_i) * (1 - p_e),
    (1, 0, 1, 1): lambda p_ns, p_i, p_e: 0.16 * p_ns * p_i * p_e,
    (1, 0, 0, 1): lambda p_ns, p_i, p_e: 0.16 * p_ns * (1 - p_i) * p_e,
    (1, 1, 1, 1): lambda p_ns, p_i, p_e: 0.84 * p_ns * p_i * p_e,
    (1, 1, 0, 1): lambda p_ns, p_i, p_e: 0.84 * p_ns * (1 - p_i) * p_e,
}
}



r_o = 100
r_i = 20
w_o = 1.5
w_i = 0
pi_o = 10
pi_i = 200
lambda_E = 1
lambda_I = 21/8 #not sure about this number
schedule = [0]*32
#give the decisions numbers, so they are comparable
d_e = 1
d_i = 2
d_o = 3
d_n = 4
policy = {}

def time(stage):
    return 9+(0.25*(stage-1))


def lambda_It(stage):
    if stage in (1,2,3,4,29,30,31,32):
        return lambda_I
    else:
        a = (2*math.pi/3)*(21-lambda_I)
        return lambda_I + a* abs(math.sin((1/3)*math.pi*(time(stage)-9)))


def p_I(stage):
    return 1 - math.e**(-lambda_It(stage)*time(stage))
def p_E(stage):
    return 1 - math.e**(-lambda_E*time(stage))
def p_NS(stage):
    if schedule[stage-1] == 0:
        return 0
    if schedule[stage-1] == 1:
        return 1



#schedule = (0,1,0,....)
#state:(n/s, o , i, e ) where all of these are just numbers

def ns(state):
    return state[0]
def o(state):
    return state[1]
def i(state):
    return state[2]
def e(state):
    return state[3]


def revenue(state,decision, stage):
    if stage == 33:
        return -o(state)*pi_o - i(state)*pi_i
    else:
        if decision == d_e:
            if ns(state) == 0: #nobody scheduled
                return -i(state)*w_i-o(state)*w_o
            if ns(state) == 1: #somebody scheduled
                return -i(state)*w_i-(0.84+o(state))*w_o
            else:
                return 0
        if decision == d_i:
            if ns(state) == 0:
                return r_i - o(state)*w_o - (i(state)-1)*w_i
            if ns(state) == 1:
                return r_i - (o(state)+0.84)*w_o-(i(state)-1)*w_i
            else:
                return 0
        if decision == d_o:
            if ns(state) == 1:
                return r_o - o(state)*w_o -i(state)*w_i
            if ns(state) ==0:
                return r_o - (o(state)-1)*w_o - i(state)*w_i
            else:
                return 0
        if decision == d_n:
                return - o(state)*w_o -i(state)*w_i


#transition probabilities
def transition_prob(state,decision,stage,nextstate):
    delta = (ns(nextstate),o(nextstate)-o(state),i(nextstate)-i(state),e(nextstate)-e(state))
    if delta not in TRANSITIONS[decision]:
        return 0
    p_i = p_I(stage)
    p_e = p_E(stage)
    if stage >= 32:
        p_ns = 0
    else:
        if ns(nextstate) == schedule[stage]:
            p_ns = 1
        else:
            p_ns = 0

    return TRANSITIONS[decision][delta](
        p_ns,
        p_i,
        p_e,
    )

def nextpossiblestates(state,decision,stage):
    nextstates = []

    if decision == d_e:
        if stage == 32 or schedule[stage] == 0:
            possible_changes = ((0, 0, 0, -1),(0, 0, 1, -1),(0, 0, 0, 0),(0, 0, 1, 0))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates
        if schedule[stage] == 1: #ns intentionaly changed to 0, so I dont add that
            possible_changes = ((0, 0, 0, -1),(0, 0, 1, -1),(0, 1, 0, -1),(0, 1, 1, -1),(0, 0, 0, 0),(0, 0, 1, 0),(0, 1, 0, 0),(0, 1, 1, 0))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates
    if decision == d_i:
        if stage == 32 or schedule[stage] == 0:
            possible_changes = ((0, 0, 0, 0),(0, 0,-1, 0),(0, 0, 0, 1),(0, 0,-1, 1))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates
        if schedule[stage] == 1:
            possible_changes = ((0, 0, 0, 0),(0, 0,-1, 0),(0, 1, 0, 0),(0, 1,-1, 0),(0, 0, 0, 1),(0, 0,-1, 1),(0, 1, 0, 1),(0, 1,-1, 1))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates
    if decision == d_o:
        if stage == 32 or schedule[stage] == 0:
            possible_changes = ((0,-1, 0, 0),(0,-1, 1, 0),(0,-1, 0, 1),(0,-1, 1, 1))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates
        if schedule[stage] == 1:
            possible_changes = ((0, 0, 0, 0),(0, 0, 1, 0),(0,-1, 0, 0),(0,-1, 1, 0),(0, 0, 0, 1),(0, 0, 1, 1),(0,-1, 0, 1),(0,-1, 1, 1))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates
    if decision == d_n:
        if stage == 32 or schedule[stage] == 0:
            possible_changes = ((0, 0, 1, 0),(0, 0, 0, 0),(0, 0, 1, 1),(0, 0, 0, 1))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates
        if schedule[stage] == 1:
            possible_changes = ((0, 0, 1, 0),(0, 0, 0, 0),(0, 1, 1, 0),(0, 1, 0, 0),(0, 0, 1, 1),(0, 0, 0, 1),(0, 1, 1, 1),(0, 1, 0, 1))
            for i in possible_changes:
                nextstates.append([a + b for a, b in zip(i, state)])
            return nextstates


V = {}
reachable = {}
decisions = (d_n,d_o,d_i,d_e)
def backwardsolution():
    reachable[1] = {(0, 0, 0, 0)}
    for stage in range(1, 33):
        reachable[stage + 1] = set()

        for state in reachable[stage]:
            for decision in decisions:
                for next_state in nextpossiblestates(state, decision, stage):
                    reachable[stage + 1].add(next_state)
    '''
    stage = 33
    ns = 0
    for o in range(stage):
        for i in range(stage):
            for e in range(stage):
                state = (ns, o, i, e)
                V[(33,state)] = revenue(state,0,33)
    for stagei in range(32,0,-1):
        ns = schedule[stagei-1]
        for o in range(stagei):
            for i in range(stagei):
                for e in range(stagei):
    '''
                    state = (ns, o, i, e)
                    bestvalue = -float("inf")
                    bestdecision = None

                    decisions = []
                    if i > 0 and e == 0:
                        decisions.append(d_i)

                    if e > 0:
                        decisions.append(d_e)

                    if o > 0 and e == 0:
                        decisions.append(d_o)

                    if o == 0 and i == 0 and e == 0:
                        decisions.append(d_n)

                    for decision in decisions:
                        val = revenue(state,decision, stagei)

                        for nextst in nextposiiblestates(state, decision, stagei):
                            val += (transition_prob(state,decision,stagei,nextst)*V[(stagei+1,tuple(nextst))])

                        if val > bestvalue:
                            bestvalue = val
                            bestdecision = decision

                    V[(stagei,state)] = bestvalue
                    policy[(stagei,state)] = bestdecision
    return V,policy



'''
def recurrence_relation(stage, state):
    if stage == 33:
        return revenue(state,0, 33), None #independent of the decision
    else:
        values = {}

        if i(state) > 0 and e(state)== 0:
            values["d_i"] = revenue(state, d_i, stage) + sumrec(state, d_i, stage)

        if e(state) > 0:
            values["d_e"] = revenue(state, d_e, stage) + sumrec(state, d_e, stage)

        if o(state) > 0 and e(state) == 0:
            values["d_o"] = revenue(state, d_o, stage) + sumrec(state, d_o, stage)

        if sum(state[1:]) == 0:
            values["d_n"] = revenue(state, d_n, stage) + sumrec(state, d_n, stage)

        best_decision = max(values, key=values.get)
        best_value = values[best_decision]
        policy[(stage, tuple(state))] = best_decision
        return best_value, best_decision


def sumrec(state, decision, stage):
    total = 0
    for st in nextpossiblestates(state, decision, stage):
        total += (
            transition_prob(state, decision, stage, st)
            * recurrence_relation(stage+1, tuple(st))[0]
        )
    return total
'''
print(backwardsolution())

#print(nextposiiblestates((2,0,0,0)))