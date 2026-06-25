
import math

TRANSITIONS = {

'd_i': {

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


'd_o': {

    # n-state transitions
    (0, 0, 0, 0): lambda p_ns,p_i,p_e: 0,
    (0,-1, 0, 0): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*(1-p_e),
    (0, 0, 1, 0): lambda p_ns,p_i,p_e: 0,
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


'd_e': {

    # n-state transitions
    (0, 0, 0, 0): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*(1-p_e),
    (0, 0, 1, 0): lambda p_ns,p_i,p_e: p_ns*p_i*(1-p_e),
    (0, 0, 0, 1): lambda p_ns,p_i,p_e: p_ns*(1-p_i)*p_e,
    (0, 0, 1, 1): lambda p_ns,p_i,p_e: p_ns*p_i*p_e,

    # s-state transitions
    (1, 0, 0, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*(1-p_e),
    (1, 0, 1, 0): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*(1-p_e),
    (1, 1, 0, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*(1-p_e),
    (1, 1, 1, 0): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*(1-p_e),
    (1, 0, 0, 1): lambda p_ns,p_i,p_e: 0.16*p_ns*(1-p_i)*p_e,
    (1, 0, 1, 1): lambda p_ns,p_i,p_e: 0.16*p_ns*p_i*p_e,
    (1, 1, 0, 1): lambda p_ns,p_i,p_e: 0.84*p_ns*(1-p_i)*p_e,
    (1, 1, 1, 1): lambda p_ns,p_i,p_e: 0.84*p_ns*p_i*p_e,
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


def time(stage):
    return 9+(0.25*(stage-1))


def lambda_It(stage):
    if stage in (1,2,3,4,29,30,31,32):
        return lambda_I
    else:
        a = (2*math.pi/3)*(21-lambda_I)
        return lambda_I + a* abs(math.sin((1/3)*math.pi*(time(stage)-9)))


def p_I(stage):
    return math.e**(-lambda_It(stage)*time(stage))*lambda_It(stage)*time(stage)

def p_E(stage):
    return math.e**(-lambda_E*time(stage))*lambda_E*time(stage)
def p_NS(stage):
    if schedule[stage] == 0:
        return 0
    if schedule[stage] == 1:
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
        if decision == d_i:
            if ns(state) == 0:
                return r_i - o(state)*w_o - (i(state)-1)*w_i
            if ns(state) == 1:
                return r_i - (o(state)+0.84)*w_o-(i(state)-1)*w_i
        if decision == d_o:
            if ns(state) == 1:
                return r_o - o(state)*w_o -i(state)*w_i
            if ns(state) ==0:
                return r_o - (o(state)-1)*w_o - i(state)*w_i


#transition probabilities
def transition_prob(state,decision,stage,nextstate):
    delta = (ns(nextstate),o(nextstate)-o(state),i(nextstate)-i(state),e(nextstate)-e(state))
    if delta not in TRANSITIONS[decision]:
        return 0
    p_i = p_I(stage)
    p_e = p_E
    p_ns = p_NS(stage)

    return TRANSITIONS[decision][delta](
        p_ns,
        p_i,
        p_e,
    )

def recurrence_relation(stage, state):
    if stage == 33:
        return revenue(33,0, stage) #independent of the decision
    else:
        return max(revenue(state,d_i,stage)+ )


