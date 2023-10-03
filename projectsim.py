import random
import simpy


RANDOM_SEED = random.randint(1, 1000000)
SIM_TIME = 100000       # Simulation time in minutes

T1 = 20                 # Number of T1 operators
T2 = 2                  # Number of T2 operators
T1_TIMETOSOLVE = 5      # Time in minutes T1 has to solve ticket
T2_TIMETOSOLVE = 30     # Time in minutes T2 has to solve ticket
T2_SUPERIORITY = 2      # Determines how much better T2 is than T1

TICKETS = 80            # Number of tickets to solve
SOLVERATE = (.1, 10)    # From-to % per minute to solve ticket, (One decimal accuracy)

DEBUG_LOG = False
UNSOLVED_LOG = False

TICKETS_SOLVED_T1 = 0
TICKETS_SOLVED_T2 = 0
T1_TOTAL_SOLVE_TIME = 0
T2_TOTAL_SOLVE_TIME = 0
TICKETS_DISCARDED = 0
LOW_DISCARD = SOLVERATE[1] * T2_SUPERIORITY
HIGH_DISCARD = 0
LAST_SOLVED = 0


class Callcenter(object):

    def __init__(self, env, t1, t2):
        self.env = env
        self.t1 = simpy.Resource(env, t1)
        self.t2 = simpy.Resource(env, t2)

    def solve(self, name, solverate, ticket_type):
        global TICKETS_SOLVED_T1
        global TICKETS_SOLVED_T2
        global T1_TOTAL_SOLVE_TIME
        global T2_TOTAL_SOLVE_TIME
        global TICKETS_DISCARDED
        global HIGH_DISCARD
        global LOW_DISCARD
        global LAST_SOLVED

        tts = 0
        while 1:
            yield self.env.timeout(1)
            tts += 1
            solved = random.randint(1, 1000)
            if solved <= solverate: break
            if ticket_type == 1 and tts >= T1_TIMETOSOLVE: break
            if ticket_type == 2 and tts >= T2_TIMETOSOLVE: break
            

        if ticket_type == 1:
            if solved > solverate:
                if UNSOLVED_LOG: print(f"{name} unsolved at T1 sent to T2, solverate: {solverate/10}%")
                env.process(ticket(env, name, solverate * T2_SUPERIORITY, self, 2))
                return
            else:
                TICKETS_SOLVED_T1 += 1
                if DEBUG_LOG: print(f"{name}, T{ticket_type} ticket, solved at {env.now}, time: {tts}")
                if env.now > LAST_SOLVED: LAST_SOLVED = env.now
                T1_TOTAL_SOLVE_TIME += tts
                return
        
        elif ticket_type == 2:
            if solved > solverate:
                TICKETS_DISCARDED += 1
                if UNSOLVED_LOG: print(f"{name} unsolved at T2, Discarded, Solverate: {solverate/10}%")
                if solverate/T2_SUPERIORITY < LOW_DISCARD: LOW_DISCARD = solverate/T2_SUPERIORITY
                if solverate/T2_SUPERIORITY > HIGH_DISCARD: HIGH_DISCARD = solverate/T2_SUPERIORITY
                return
            else:
                TICKETS_SOLVED_T2 += 1
                if DEBUG_LOG: print(f"{name}, T{ticket_type} ticket, solved at {env.now}, time: {tts}")
                if env.now > LAST_SOLVED: LAST_SOLVED = env.now
                T2_TOTAL_SOLVE_TIME += tts
                return


def ticket(env, name, solverate, cc, ticket_type):
    if ticket_type == 1:
        with cc.t1.request() as request:
            yield request
            if DEBUG_LOG: print(f"{name}, T{ticket_type}, Started solving ticket at {env.now}")
            yield env.process(cc.solve(name, solverate, ticket_type))

    elif ticket_type == 2:
        with cc.t2.request() as request:
            yield request   
            if DEBUG_LOG: print(f"{name}, T{ticket_type}, Started solving ticket at {env.now}")
            yield env.process(cc.solve(name, solverate, ticket_type))



def setup(env, t1, t2, tickets, sr):

    callcenter = Callcenter(env, t1, t2)

    for i in range(tickets):
        solverate = random.randint(sr[0]*10, sr[1]*10)
        env.process(ticket(env, 'Ticket %d' % i, solverate, callcenter, ticket_type = 1))

    while 1:
        yield env.timeout(1)



random.seed(RANDOM_SEED)
env = simpy.Environment()
env.process(setup(env, T1, T2, TICKETS, SOLVERATE))

env.run(until=SIM_TIME)

print(f"Total Tickets: {TICKETS}\n")
print(f"T1 Solved: {TICKETS_SOLVED_T1}, Avg: {round(T1_TOTAL_SOLVE_TIME/TICKETS_SOLVED_T1,2)}m")
print(f"T2 Solved: {TICKETS_SOLVED_T2}, Avg: {round(T2_TOTAL_SOLVE_TIME/TICKETS_SOLVED_T2,2)}m\n")
print(f"Tickets Discarded: {TICKETS_DISCARDED} ({round(TICKETS_DISCARDED/TICKETS*100,2)}%)")
print(f"Lowest: {LOW_DISCARD/10}%, Highest: {HIGH_DISCARD/10}%\n")
print(f"Last Ticket Solved At: {LAST_SOLVED//60}h {LAST_SOLVED%60}m")