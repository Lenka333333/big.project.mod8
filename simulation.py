import numpy as np
import math
import random

#from core import Simulation, Event
#from statistics import TimeWeightedStatistic, SampleStatistic, Counter, _t_critical
#from distributions import Exponential, Erlang

patient_count = 0

random.seed(42)

# office_start = 8.0  # 08:00
# office_end = 16.0  # 16:00
# weekday_count = 5  # mon–fri
# day = time%24
# week = day%7


lambda_e = 1

# lambda_i_base = 0
# lambda_i_amplitude = 0


lambda_i_base = 0.375
lambda_i_amplitude = 1.5 * math.pi
lambda_i_max = lambda_i_base + lambda_i_amplitude  # change with sine


def lambda_i(time):
    if not weekday_check(time):
        return lambda_i_base
    h = time % 24
    if 9 <= h < 12:
        return lambda_i_base + lambda_i_amplitude * math.sin(math.pi * (h - 9) / 3)
    elif 12 <= h < 15:
        return lambda_i_base + lambda_i_amplitude * math.sin(math.pi * (h - 12) / 3)
    return lambda_i_base


lambda_o = 2.875
# lambda_o = 0
p_show = 0.84

mu = 4.138  # service rate

slots_morning = 4
slots_afternoon = 3


def slots(hour):
    if 8 <= hour < 12:
        return slots_morning
    elif 12 <= hour < 16:
        return slots_afternoon
    else:
        return 0


chair_limit = 16 #from analysis of question5

warmup_hours = 50 * 7 * 24
total_hours = 200 * 7 * 24  # add weeks to improve precision
data_hours = total_hours - warmup_hours
n_batches = 30
batch_hours = data_hours / n_batches

pt_e = "emergency"  # changed incase conflict
pt_i = "inpatient"
pt_o = "outpatient"

sc1 = 0  # index/ maybe not hard coded  original scanner_x
sc2 = 1
num_scanners = 2


def mean(numbers):
    total = 0
    for x in numbers:
        total = total + x
    return total / len(numbers)  # only because this is more convenient than the des liabray


def deviation(numbers):
    n = len(numbers)
    if n < 2:
        return float('nan')
    m = mean(numbers)
    sum_sq = 0
    for x in numbers:
        sum_sq = sum_sq + (x - m) ** 2
    return math.sqrt(sum_sq / (n - 1))


def schedule(future_list, event_time, event_type, data=None):
    event = [event_time, event_type, data]  # use list for event then add
    for i in range(len(future_list)):
        if future_list[i][0] > event_time:
            future_list.insert(i, event)
            return
    future_list.append(event)


def day_number(t):
    return int(t / 24)


def week_day(t):
    return int(t / 24) % 7


def weekday_check(t):
    if week_day(t) < 5:
        return True
    else:
        return False


def is_office_hours(t):
    if not weekday_check(t):
        return False
    h = t % 24
    if 8 <= h < 16:
        return True
    else:
        return False


def start_working(t):
    d = int(t / 24)
    h = t % 24
    if d % 7 < 5:
        if h < 8:
            return d * 24 + 8
        if h < 16:
            return t
    d = d + 1
    for i in range(10):
        if d % 7 < 5:
            return d * 24 + 8
        d = d + 1  # if not increasing date then will have nonetype loop


def office_hour(start_t, oh):
    t = start_working(start_t)
    while oh > 1e-12:  # >0
        d = int(t / 24)
        oh_end = d * 24 + 16
        oh_left = oh_end - t
        if oh_left >= oh:
            return t + oh
        else:
            oh = oh - oh_left
            t = start_working(oh_end)
    return t


def next_friday(t):
    d = int(t / 24)
    h = t % 24
    di = (4 - d % 7) % 7
    if di == 0 and h >= 16:
        di = 7
    return (d + di) * 24 + 16


def next_weekday(t):
    d = int(t / 24) + 1
    for i in range(10):
        if d % 7 < 5:
            return d * 24 + 8
        d = d + 1  # nonetype prevent


def next_loop(t):
    d = int(t / 24)
    h = t % 24
    dow = d % 7
    if dow < 5:
        if h < 8:
            return d * 24 + 8
        elif h < 16:
            return d * 24 + 16
        else:
            return (d + 1) * 24
    else:
        di = 7 - dow
        return (d + di) * 24


def slots_week(slot_table, mon):
    for day_offset in range(5):
        d = mon + day_offset

        for hour in range(8, 16):

            for s in range(slots(hour)):
                key = (d, hour, s)

                if key not in slot_table:
                    slot_table[key] = None


def slot_begin(slot_table, earliest_day, latest_day):
    for d in range(earliest_day, latest_day + 1):

        if d % 7 >= 5:
            continue

        for hour in range(8, 16):

            for s in range(slots(hour)):
                if slot_table.get((d, hour, s)) is None:
                    return (d, hour, s)
    return None


def slot_to_time(d, hour, s):
    n = slots(hour)

    if n == 0:
        return d * 24 + hour
    return d * 24 + s / n + hour


def patient_new(type, t):
    global patient_count
    patient_count = patient_count + 1
    p = {}

    p['pid'] = patient_count
    p['type'] = type
    p['request_t'] = t
    p['arrival_t'] = t

    p['request_day'] = day_number(t)

    p['svc_start'] = None
    p['svc_end'] = None
    p['outside_room'] = False

    p['appt_t'] = None

    p['appt_day'] = None
    p['oh_request'] = False
    p['oh_req_day'] = None
    return p


class Scanning:
    def __init__(self):
        self.patient = 0

        self.future_list = []
        self.t = 0

        self.emergency_queue = []  # with prioity
        self.queue_normal = []
        self.waiting_list = []  # draw this  from index0 to normal
        # scheduled =(0,1,0,...)
        self.warmup_done = False
        self.sc_busy = [False, False]
        self.sc_available = [True, False]

        self.sc_busy_since = [None, None]

        self.sc_patient = [None, None]
        self.slot_table = {}

        self.batch_busy_oh = [0, 0]
        self.batch_busy_noh = [0, 0]
        self.batch_oh_dur = 0
        self.batch_noh_dur = 0

        self.period_t = 0
        # self.sc1_oh_util = SampleStatistic()
        # self.sc2_oh_util = SampleStatistic()
        # self.sc1_noh_util = SampleStatistic()
        self.b_sc1_oh = []
        self.b_sc2_oh = []
        self.b_sc1_noh = []

        # self.b_op_acc = SampleStatistic()
        self.b_op_acc = []
        self.b_em_wait = []
        self.b_op_wait = []
        self.b_ovfl = []
        self.b_inp_rate = []

        self.cur_op_acc = []  # SampleStatistic()
        self.cur_em_wait = []
        self.cur_op_wait = []
        self.cur_ovfl = []
        self.cur_inp_rate = []


def period_update(sim, time):
    t = sim.period_t
    while t < time - 1e-12:

        boundary = next_loop(t)

        next = min(boundary, time)
        dt = next - t
        if is_office_hours(t):

            sim.batch_oh_dur += dt
        else:
            sim.batch_noh_dur += dt
        t = next
    sim.period_t = time


def busy(sim, sc_idx, from_t, to_t):
    t = from_t
    while t < to_t - 1e-12:

        boundary = next_loop(t)
        next = min(boundary, to_t)
        dt = next - t

        if is_office_hours(t):
            sim.batch_busy_oh[sc_idx] += dt

        else:
            sim.batch_busy_noh[sc_idx] += dt
        t = next


def freesc(sim):
    if sim.sc_available[sc2] and not sim.sc_busy[sc2]:
        return sc2
    if sim.sc_available[sc1] and not sim.sc_busy[sc1]:
        return sc1
    return None


def start_scan(sim, sc_idx, patient):
    duration = random.uniform(10, 19) / 60  # in main project/ change to minutes
    sim.sc_busy[sc_idx] = True

    sim.sc_patient[sc_idx] = patient
    sim.sc_busy_since[sc_idx] = sim.t

    patient['svc_start'] = sim.t
    schedule(sim.future_list, sim.t + duration, "scan", {'sc': sc_idx})


def start_service(sim, patient, wait_hours):
    if not sim.warmup_done:
        return

    type = patient['type']
    if patient['outside_room']:
        overflow = 1
    else:
        overflow = 0
    sim.cur_ovfl.append(overflow)

    if type == pt_e:

        sim.cur_em_wait.append(wait_hours)
    elif type == pt_o:
        sim.cur_op_wait.append(wait_hours)

    if type == pt_i and patient['oh_request']:

        deadline = patient['oh_req_day'] * 24 + 16
        if sim.t >= deadline:  # maybe should be t + expected scan duration? or we just think of starting time?
            missed = 1
            # missed.increment() need counter()
        else:
            missed = 0
        sim.cur_inp_rate.append(missed)
        # sim.inp_rate_total += 1
        # sim.inp_rate_miss += missed


def next_scan(sim, sc_idx):
    if len(sim.emergency_queue) > 0:
        next_p = sim.emergency_queue.pop(0)
    elif len(sim.queue_normal) > 0:
        next_p = sim.queue_normal.pop(0)
    else:
        return

    wait = sim.t - next_p['arrival_t']

    start_service(sim, next_p, wait)
    start_scan(sim, sc_idx, next_p)


def update_queue(sim, patient):
    total_waiting = len(sim.emergency_queue) + len(sim.queue_normal)

    if total_waiting >= chair_limit:
        patient['outside_room'] = True

    if patient['type'] == pt_e:
        sim.emergency_queue.append(patient)
    else:
        sim.queue_normal.append(patient)


def next_inp(t):
    while True:
        t = t + random.expovariate(lambda_i_max)

        if random.random() <= lambda_i(t) / lambda_i_max:
            return t


# class Emergency(Event):
#    def execute(self, sim):
#        ct = sim.ct
#        t = sim.current_time
#        sim.schedule(EmergencyArrival(t + random.expovariate(ct.lambda_e)))

#  #      p = patient_new(ct, pt_e, t)

#        sc = find_free_scanner(ct)
#        if sc is not None:
#            service_start(sim, p, 0.0)
#            start_scan(sim, sc, p)
#        else:
#            set to queue(ct, p)


def eme_arrive(sim):
    t = sim.t
    schedule(sim.future_list, t + random.expovariate(lambda_e), "eme_arrival")

    patient = patient_new(pt_e, t)
    sc = freesc(sim)

    if sc is not None:
        start_service(sim, patient, wait_hours=0)
        start_scan(sim, sc, patient)
    else:
        update_queue(sim, patient)


def inp_arrive(sim):
    t = sim.t
    schedule(sim.future_list, next_inp(t), "inp_arrival")
    patient = patient_new(pt_i, t)
    patient['oh_request'] = is_office_hours(t)
    patient['oh_req_day'] = day_number(t)
    sc = freesc(sim)
    if sc is not None:
        start_service(sim, patient, wait_hours=0)
        start_scan(sim, sc, patient)
    else:
        update_queue(sim, patient)  # forget to send


def op_called(sim):
    t = sim.t
    next_call = office_hour(t, random.expovariate(lambda_o))

    schedule(sim.future_list, next_call, "op_call")
    patient = patient_new(pt_o, t)

    earliest_day = day_number(t) + 1

    this_friday = day_number(t) + (4 - week_day(t))

    if earliest_day > this_friday:
        sim.waiting_list.append(patient)
        return

    monday_this_week = day_number(t) - week_day(t)
    slots_week(sim.slot_table, monday_this_week)

    found = slot_begin(sim.slot_table, earliest_day, this_friday)

    if found is not None:
        d, hour, s = found
        sim.slot_table[(d, hour, s)] = patient['pid']

        patient['appt_t'] = slot_to_time(d, hour, s)
        patient['appt_day'] = d

        if random.random() <= p_show:
            schedule(sim.future_list, patient['appt_t'], "op_arrival", {'p': patient})
    else:
        sim.waiting_list.append(patient)


def op_arrive(sim, patient):
    t = sim.t
    patient['arrival_t'] = t

    if sim.warmup_done:
        access = patient['appt_day'] - patient['request_day']
        sim.cur_op_acc.append(access)

    sc = freesc(sim)
    if sc is not None:

        start_service(sim, patient, wait_hours=0)

        start_scan(sim, sc, patient)
    else:
        update_queue(sim, patient)


def schedule(future_list, event_time, event_type, data=None):
    event = [event_time, event_type, data]  # use list for event then add
    for i in range(len(future_list)):
        if future_list[i][0] > event_time:
            future_list.insert(i, event)
            return
    future_list.append(event)


def scan_finish(sim, scanner):
    t = sim.t
    patient = sim.sc_patient[scanner]

    patient['svc_end'] = t

    if sim.warmup_done and sim.sc_busy_since[scanner] is not None:
        busy(sim, scanner, sim.sc_busy_since[scanner], t)

    sim.sc_busy[scanner] = False
    sim.sc_patient[scanner] = None
    sim.sc_busy_since[scanner] = None

    if scanner == sc2 and not sim.sc_available[sc2]:
        return

    next_scan(sim, scanner)


def sc2_open(sim):
    t = sim.t
    schedule(sim.future_list, t + 24, "open_sc2")

    if not weekday_check(t):
        return

    sim.sc_available[sc2] = True
    if not sim.sc_busy[sc2]:
        next_scan(sim, sc2)


def sc2_close(sim):
    t = sim.t
    schedule(sim.future_list, t + 24, "close_sc2")

    if not weekday_check(t):
        return
    sim.sc_available[sc2] = False


def friday_batch(sim):
    t = sim.t
    schedule(sim.future_list, t + 7 * 24, "friday")

    monday_next_week = day_number(t) + 3  # date fix
    slots_week(sim.slot_table, monday_next_week)

    while len(sim.waiting_list) > 0:
        p = sim.waiting_list[0]

        found = slot_begin(sim.slot_table, monday_next_week, monday_next_week + 4)

        if found is not None:
            sim.waiting_list.pop(0)
            d, hour, s = found

            sim.slot_table[(d, hour, s)] = p['pid']

            p['appt_t'] = slot_to_time(d, hour, s)
            p['appt_day'] = d

            if random.random() <= p_show:
                schedule(sim.future_list, p['appt_t'], "op_arrival", {'p': p})
        else:
            break


def warmup(sim):
    sim.warmup_done = True
    sim.period_t = sim.t

    for i in range(2):

        if sim.sc_busy[i]:
            sim.sc_busy_since[i] = sim.t

    schedule(sim.future_list, sim.t + batch_hours, "batch")


def batch(sim):
    period_update(sim, sim.t)

    for i in range(2):

        if sim.sc_busy[i] and sim.sc_busy_since[i] is not None:
            busy(sim, i, sim.sc_busy_since[i], sim.t)

            sim.sc_busy_since[i] = sim.t

    if sim.batch_oh_dur > 0:
        sim.b_sc1_oh.append(sim.batch_busy_oh[sc1] / sim.batch_oh_dur)
        sim.b_sc2_oh.append(sim.batch_busy_oh[sc2] / sim.batch_oh_dur)
    else:
        sim.b_sc1_oh.append(0)
        sim.b_sc2_oh.append(0)

    if sim.batch_noh_dur > 0:
        sim.b_sc1_noh.append(sim.batch_busy_noh[sc1] / sim.batch_noh_dur)
    else:
        sim.b_sc1_noh.append(0)

    sim.b_op_acc.append(mean(sim.cur_op_acc))
    sim.b_em_wait.append(mean(sim.cur_em_wait))
    sim.b_op_wait.append(mean(sim.cur_op_wait))

    sim.b_ovfl.append(mean(sim.cur_ovfl))

    sim.b_inp_rate.append(mean(sim.cur_inp_rate))

    sim.batch_busy_oh = [0, 0]
    sim.batch_busy_noh = [0, 0]
    sim.batch_oh_dur = 0
    sim.batch_noh_dur = 0

    sim.cur_op_acc = []
    sim.cur_em_wait = []
    sim.cur_op_wait = []
    sim.cur_ovfl = []
    sim.cur_inp_rate = []  # for missing ddl

    if sim.t + batch_hours < total_hours:
        schedule(sim.future_list, sim.t + batch_hours, "batch")


def simulation():
    global patient_count
    patient_count = 0
    sim = Scanning()
    fl = sim.future_list
    schedule(fl, 0, "eme_arrival")
    schedule(fl, next_inp(0), "inp_arrival")
    schedule(fl, 8, "op_call")
    schedule(fl, 8, "open_sc2")
    schedule(fl, 16, "close_sc2")
    schedule(fl, next_friday(0), "friday")  # time fix
    schedule(fl, warmup_hours, "warmup")
    schedule(fl, total_hours, "endsim")
    while len(fl) > 0:
        ev_time, ev_type, ev_data = fl.pop(0)
        if sim.warmup_done:
            period_update(sim, ev_time)
        sim.t = ev_time
        if ev_type == "eme_arrival":
            eme_arrive(sim)
        elif ev_type == "inp_arrival":
            inp_arrive(sim)
        elif ev_type == "op_call":
            op_called(sim)
        elif ev_type == "op_arrival":
            op_arrive(sim, ev_data['p'])
        elif ev_type == "scan":
            scan_finish(sim, ev_data['sc'])
        elif ev_type == "open_sc2":
            sc2_open(sim)
        elif ev_type == "close_sc2":
            sc2_close(sim)
        elif ev_type == "friday":
            friday_batch(sim)
        elif ev_type == "warmup":
            warmup(sim)
        elif ev_type == "batch":
            batch(sim)
        elif ev_type == "endsim":
            break
    return sim


if __name__ == "__main__":

    def ci_width(data_list):
        clean = [x for x in data_list if not math.isnan(x)]
        n = len(clean)
        m = mean(clean)

        s = 0

        for x in clean:
            s = s + (x - m) ** 2

        dev = math.sqrt(s / (n - 1))  # deviation
        return 2.04523 * (dev / (n ** 0.5))


    def ci(data_list):
        clean = [x for x in data_list if not math.isnan(x)]
        m = mean(clean)
        hw = ci_width(clean)

        l = m - hw
        u = m + hw
        return l, u


    def print_res(name, data_list):
        m = mean(data_list)
        hw = ci_width(data_list)
        l, u = ci(data_list)
        print(name + "_mean:", m)
        print(name + "_ci_half_width:", hw)
        print(name + "_ci:", f"[{l},{u}]")


    sim = simulation()
    print_res("sc1_oh_util", sim.b_sc1_oh)
    print_res("sc2_oh_util", sim.b_sc2_oh)
    print_res("sc1_noh_util", sim.b_sc1_noh)
    print_res("op_access_days", sim.b_op_acc)
    print_res("emergency_wait_hours", sim.b_em_wait)
    print_res("outpatient_wait_hours", sim.b_op_wait)
    print_res("overflow_fraction", sim.b_ovfl)
    print_res("inp_rate_failure_rate", sim.b_inp_rate)
