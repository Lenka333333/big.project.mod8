import math
import random

patient_count = 0
random.seed(42)
lambda_e = 1.0
lambda_i_base = 0.375
lambda_i_amp = 1.5 * math.pi
lambda_i_max = lambda_i_base + lambda_i_amp
lambda_o = 2.875
p_show = 0.84

mu = 60.0 / 14.5
chair_limit = 14

Q3_OP_SLOTS = {8: 8, 9: 6, 10: 0, 11: 4, 12: 6, 13: 0, 14: 4, 15: 8}


def slots_for_hour(hour):
    return Q3_OP_SLOTS.get(hour, 0)


warmup_hours = 50 * 7 * 24
total_hours = 200 * 7 * 24
n_batches = 30
batch_hours = (total_hours - warmup_hours) / n_batches

pt_e, pt_i, pt_o = "emergency", "inpatient", "outpatient"
sc1, sc2 = 0, 1


def mean(lst):
    lst = [x for x in lst if x == x]
    return sum(lst) / len(lst) if lst else float('nan')


def schedule(fl, t, ev_type, data=None):
    ev = [t, ev_type, data]
    for i in range(len(fl)):
        if fl[i][0] > t:
            fl.insert(i, ev)
            return
    fl.append(ev)


def day_number(t):    return int(t / 24)


def week_day(t):      return int(t / 24) % 7


def weekday_check(t): return week_day(t) < 5


def is_office_hours(t):
    return weekday_check(t) and (8 <= t % 24 < 16)


def start_working(t):
    d = int(t / 24)
    h = t % 24
    if d % 7 < 5 and 8 <= h < 16: return t
    if d % 7 < 5 and h < 8: return d * 24 + 8
    d += 1
    for _ in range(10):
        if d % 7 < 5: return d * 24 + 8
        d += 1


def office_hour(start_t, oh):
    t = start_working(start_t)
    while oh > 1e-12:
        d = int(t / 24)
        oh_end = d * 24 + 16
        oh_left = oh_end - t
        if oh_left >= oh: return t + oh
        oh -= oh_left
        t = start_working(oh_end)
    return t


def next_friday(t):
    d = int(t / 24)
    h = t % 24
    di = (4 - d % 7) % 7
    if di == 0 and h >= 16: di = 7
    return (d + di) * 24 + 16


def next_loop(t):
    d = int(t / 24)
    h = t % 24
    dow = d % 7
    if dow < 5:
        if h < 8:  return d * 24 + 8
        if h < 16: return d * 24 + 16
        return (d + 1) * 24
    return (d + 7 - dow) * 24


def lambda_i(t):
    if not weekday_check(t): return lambda_i_base
    h = t % 24
    if 9 <= h < 12: return lambda_i_base + lambda_i_amp * math.sin(math.pi * (h - 9) / 3)
    if 12 <= h < 15: return lambda_i_base + lambda_i_amp * math.sin(math.pi * (h - 12) / 3)
    return lambda_i_base


def next_inp(t):
    while True:
        t += random.expovariate(lambda_i_max)
        if random.random() <= lambda_i(t) / lambda_i_max:
            return t


# ADJUSTED: Only initializes slots that match actual scanner capacity limits
def slots_week(slot_table, mon, half_days):
    for day_offset in range(5):
        d = mon + day_offset
        for hour in range(8, 16):
            t_hour = d * 24 + hour
            n = slots_for_hour(hour)
            if not scanner2_available(t_hour, half_days):
                n = n // 2
            for s in range(n):
                key = (d, hour, s)
                if key not in slot_table:
                    slot_table[key] = None


# ADJUSTED: Only checks within the active capacity bound of that day part
def slot_begin(slot_table, earliest_day, latest_day, half_days):
    for d in range(earliest_day, latest_day + 1):
        if d % 7 >= 5: continue
        for hour in range(8, 16):
            n = slots_for_hour(hour)
            if not scanner2_available(d * 24 + hour, half_days):
                n = n // 2
            for s in range(n):
                if slot_table.get((d, hour, s)) is None:
                    return (d, hour, s)
    return None


# ADJUSTED: Distributes appointment timestamps smoothly matching available slots (n)
def slot_to_time(d, hour, s, half_days):
    n = slots_for_hour(hour)
    if not scanner2_available(d * 24 + hour, half_days):
        n = n // 2
    return d * 24 + hour + (s / n if n > 0 else 0)


def patient_new(ptype, t):
    global patient_count
    patient_count += 1
    return {'pid': patient_count, 'type': ptype,
            'request_t': t, 'arrival_t': t,
            'request_day': day_number(t),
            'svc_start': None, 'svc_end': None,
            'outside_room': False,
            'appt_t': None, 'appt_day': None,
            'oh_request': False, 'oh_req_day': None}


class Scanning:
    def __init__(self, is_fixed):
        self.t = 0
        self.future_list = []
        self.emergency_queue = []
        self.queue_normal = []
        self.waiting_list = []
        self.warmup_done = False
        self.sc_busy = [False, False]
        self.sc_available = [True, False]
        self.sc_busy_since = [None, None]
        self.sc_patient = [None, None]
        self.slot_table = {}
        self.batch_busy_oh = [0., 0.]
        self.batch_busy_noh = [0., 0.]
        self.batch_oh_dur = 0.
        self.batch_noh_dur = 0.
        self.period_t = 0.
        self.b_sc1_oh = []
        self.b_sc2_oh = []
        self.b_sc1_noh = []
        self.b_op_acc = []
        self.b_em_wait = []
        self.b_op_wait = []
        self.b_ovfl = []
        self.b_inp_rate = []
        self.cur_op_acc = []
        self.cur_em_wait = []
        self.cur_op_wait = []
        self.cur_ovfl = []
        self.cur_inp_rate = []

        self.is_fixed = is_fixed
        if is_fixed:
            self.sc2_half_days = 10
        else:
            self.sc2_half_days = 6

        self.batch_sc2_open_dur = 0


def period_update(sim, time):
    t = sim.period_t
    while t < time - 1e-12:
        boundary = next_loop(t)
        next_t = min(boundary, time)
        dt = next_t - t
        if is_office_hours(t):
            sim.batch_oh_dur += dt
            if scanner2_available(t, sim.sc2_half_days):
                sim.batch_sc2_open_dur += dt
        else:
            sim.batch_noh_dur += dt
        t = next_t
    sim.period_t = time


def busy(sim, idx, from_t, to_t):
    t = from_t
    while t < to_t - 1e-12:
        nxt = min(next_loop(t), to_t)
        dt = nxt - t
        if is_office_hours(t):
            sim.batch_busy_oh[idx] += dt
        else:
            sim.batch_busy_noh[idx] += dt
        t = nxt


def sc2_should_be_open(sim):
    return scanner2_available(sim.t, sim.sc2_half_days)


def freesc(sim):
    if sc2_should_be_open(sim) and not sim.sc_busy[sc2]:
        return sc2
    if not sim.sc_busy[sc1]:
        return sc1
    return None


def start_scan(sim, sc_idx, patient):
    dur = random.uniform(10, 19) / 60
    sim.sc_busy[sc_idx] = True
    sim.sc_patient[sc_idx] = patient
    sim.sc_busy_since[sc_idx] = sim.t
    patient['svc_start'] = sim.t
    schedule(sim.future_list, sim.t + dur, "scan", {'sc': sc_idx})


def start_service(sim, patient, wait_hours):
    if not sim.warmup_done: return
    sim.cur_ovfl.append(1 if patient['outside_room'] else 0)
    if patient['type'] == pt_e:
        sim.cur_em_wait.append(wait_hours)
    elif patient['type'] == pt_o:
        sim.cur_op_wait.append(wait_hours)
    if patient['type'] == pt_i and patient['oh_request']:
        deadline = patient['oh_req_day'] * 24 + 16
        sim.cur_inp_rate.append(1 if sim.t >= deadline else 0)


def next_scan(sim, sc_idx):
    if sim.emergency_queue:
        nxt = sim.emergency_queue.pop(0)
    elif sim.queue_normal:
        h = sim.t % 24
        inps = [p for p in sim.queue_normal if p['type'] == pt_i]
        ops = [p for p in sim.queue_normal if p['type'] == pt_o]

        if inps and ((h >= 9.5 and h < 14.25) or (not ops)):
            nxt = inps[0];
            sim.queue_normal.remove(nxt)
        elif ops and (h >= 12.75 and h < 13.25 and len(ops) <= 3):
            nxt = ops[0];
            sim.queue_normal.remove(nxt)
        elif ops and (h >= 13.25 and h < 14 and len(ops) <= 4):
            nxt = ops[0];
            sim.queue_normal.remove(nxt)
        elif ops and (h >= 14 and h < 14.25 and len(ops) <= 5):
            nxt = ops[0];
            sim.queue_normal.remove(nxt)
        elif inps and (h >= 12.75 and h < 13.25 and len(ops) > 3):
            nxt = inps[0];
            sim.queue_normal.remove(nxt)
        elif inps and (h >= 13.25 and h < 14 and len(ops) > 4):
            nxt = inps[0];
            sim.queue_normal.remove(nxt)
        elif inps and (h >= 14 and h < 14.25 and len(ops) > 5):
            nxt = inps[0];
            sim.queue_normal.remove(nxt)
        elif ops:
            nxt = ops[0];
            sim.queue_normal.remove(nxt)
        elif inps:
            nxt = inps[0];
            sim.queue_normal.remove(nxt)
        else:
            return
    else:
        return
    wait = sim.t - nxt['arrival_t']
    start_service(sim, nxt, wait)
    start_scan(sim, sc_idx, nxt)


def update_queue(sim, patient):
    if len(sim.emergency_queue) + len(sim.queue_normal) >= chair_limit:
        patient['outside_room'] = True
    if patient['type'] == pt_e:
        sim.emergency_queue.append(patient)
    else:
        sim.queue_normal.append(patient)


def eme_arrive(sim):
    t = sim.t
    schedule(sim.future_list, t + random.expovariate(lambda_e), "eme_arrival")
    p = patient_new(pt_e, t)
    sc = freesc(sim)
    if sc is not None:
        start_service(sim, p, 0.); start_scan(sim, sc, p)
    else:
        update_queue(sim, p)


def inp_arrive(sim):
    t = sim.t
    schedule(sim.future_list, next_inp(t), "inp_arrival")
    p = patient_new(pt_i, t)
    p['oh_request'] = is_office_hours(t)
    p['oh_req_day'] = day_number(t)
    sc = freesc(sim)
    if sc is not None:
        start_service(sim, p, 0.); start_scan(sim, sc, p)
    else:
        update_queue(sim, p)


def op_called(sim):
    t = sim.t
    schedule(sim.future_list, office_hour(t, random.expovariate(lambda_o)), "op_call")
    p = patient_new(pt_o, t)
    earliest = day_number(t) + 1
    this_fri = day_number(t) + (4 - week_day(t))
    if earliest > this_fri: sim.waiting_list.append(p); return
    mon = day_number(t) - week_day(t)

    # ADJUSTED: Added half_days tracking context
    slots_week(sim.slot_table, mon, sim.sc2_half_days)
    found = slot_begin(sim.slot_table, earliest, this_fri, sim.sc2_half_days)
    if found:
        d, hour, s = found
        sim.slot_table[(d, hour, s)] = p['pid']
        p['appt_t'] = slot_to_time(d, hour, s, sim.sc2_half_days)
        p['appt_day'] = d
        if random.random() <= p_show:
            schedule(sim.future_list, p['appt_t'], "op_arrival", {'p': p})
    else:
        sim.waiting_list.append(p)


def op_arrive(sim, patient):
    t = sim.t
    patient['arrival_t'] = t
    if sim.warmup_done:
        sim.cur_op_acc.append(patient['appt_day'] - patient['request_day'])
    sc = freesc(sim)
    if sc is not None:
        start_service(sim, patient, 0.); start_scan(sim, sc, patient)
    else:
        update_queue(sim, patient)


def scan_finish(sim, scanner):
    p = sim.sc_patient[scanner]
    p['svc_end'] = sim.t
    if sim.warmup_done and sim.sc_busy_since[scanner] is not None:
        busy(sim, scanner, sim.sc_busy_since[scanner], sim.t)
    sim.sc_busy[scanner] = False
    sim.sc_patient[scanner] = None
    sim.sc_busy_since[scanner] = None
    if scanner == sc2 and not sc2_should_be_open(sim): return
    next_scan(sim, scanner)


def scanner2_policy(waiting_size):
    if waiting_size < 4.827:
        return 6
    elif waiting_size < 21.381:
        return 7
    elif waiting_size < 37.933:
        return 8
    elif waiting_size < 54.485:
        return 9
    else:
        return 10


def scanner2_available(t, half_days):
    if not weekday_check(t): return False
    day = week_day(t)
    hour = t % 24
    morning = (8 <= hour < 12)
    if half_days == 6:
        return day <= 2
    elif half_days == 7:
        return (day <= 2) or (day == 3 and morning)
    elif half_days == 8:
        return day <= 3
    elif half_days == 9:
        return (day <= 3) or (day == 4 and morning)
    else:
        return day <= 4


def sc2_open(sim):
    schedule(sim.future_list, sim.t + 24, "open_sc2")
    if scanner2_available(sim.t, sim.sc2_half_days):
        sim.sc_available[sc2] = True
        if not sim.sc_busy[sc2]:
            next_scan(sim, sc2)
    else:
        sim.sc_available[sc2] = False


def sc2_close(sim):
    schedule(sim.future_list, sim.t + 24, "close_sc2")
    if not scanner2_available(sim.t, sim.sc2_half_days):
        sim.sc_available[sc2] = False


def friday_batch(sim):
    schedule(sim.future_list, sim.t + 7 * 24, "friday")

    if sim.is_fixed:
        sim.sc2_half_days = 10
    else:
        sim.sc2_half_days = scanner2_policy(len(sim.waiting_list))

    mon_next = day_number(sim.t) + 3

    # added half_days tracking context
    slots_week(sim.slot_table, mon_next, sim.sc2_half_days)
    while sim.waiting_list:
        p = sim.waiting_list[0]
        found = slot_begin(sim.slot_table, mon_next, mon_next + 4, sim.sc2_half_days)
        if found:
            sim.waiting_list.pop(0)
            d, hour, s = found
            sim.slot_table[(d, hour, s)] = p['pid']
            p['appt_t'] = slot_to_time(d, hour, s, sim.sc2_half_days)
            p['appt_day'] = d
            if random.random() <= p_show:
                schedule(sim.future_list, p['appt_t'], "op_arrival", {'p': p})
        else:
            break


def warmup_event(sim):
    sim.warmup_done = True
    sim.period_t = sim.t
    for i in range(2):
        if sim.sc_busy[i]: sim.sc_busy_since[i] = sim.t
    schedule(sim.future_list, sim.t + batch_hours, "batch")


def batch_event(sim):
    period_update(sim, sim.t)
    for i in range(2):
        if sim.sc_busy[i] and sim.sc_busy_since[i] is not None:
            busy(sim, i, sim.sc_busy_since[i], sim.t)
            sim.sc_busy_since[i] = sim.t
    sim.b_sc1_oh.append(sim.batch_busy_oh[sc1] / sim.batch_oh_dur if sim.batch_oh_dur > 0 else 0)
    sim.b_sc2_oh.append(sim.batch_busy_oh[sc2] / sim.batch_sc2_open_dur if sim.batch_sc2_open_dur > 0 else 0)
    sim.b_sc1_noh.append(sim.batch_busy_noh[sc1] / sim.batch_noh_dur if sim.batch_noh_dur > 0 else 0)

    def bm(lst):
        return mean(lst) if lst else float('nan')

    sim.b_op_acc.append(bm(sim.cur_op_acc))
    sim.b_em_wait.append(bm(sim.cur_em_wait))
    sim.b_op_wait.append(bm(sim.cur_op_wait))
    sim.b_ovfl.append(bm(sim.cur_ovfl) if sim.cur_ovfl else 0.)
    sim.b_inp_rate.append(bm(sim.cur_inp_rate) if sim.cur_inp_rate else 0.)
    sim.batch_busy_oh = [0., 0.];
    sim.batch_busy_noh = [0., 0.]
    sim.batch_oh_dur = 0.;
    sim.batch_noh_dur = 0.
    sim.batch_sc2_open_dur = 0.
    sim.cur_op_acc = [];
    sim.cur_em_wait = [];
    sim.cur_op_wait = []
    sim.cur_ovfl = [];
    sim.cur_inp_rate = []
    if sim.t + batch_hours < total_hours:
        schedule(sim.future_list, sim.t + batch_hours, "batch")


def simulation(is_fixed):
    global patient_count
    patient_count = 0
    sim = Scanning(is_fixed)
    fl = sim.future_list
    schedule(fl, 0, "eme_arrival")
    schedule(fl, next_inp(0), "inp_arrival")
    schedule(fl, 8, "op_call")
    schedule(fl, 8, "open_sc2")
    schedule(fl, 12, "close_sc2")
    schedule(fl, 16, "close_sc2")
    schedule(fl, next_friday(0), "friday")
    schedule(fl, warmup_hours, "warmup")
    schedule(fl, total_hours, "endsim")
    while fl:
        ev_time, ev_type, ev_data = fl.pop(0)
        if sim.warmup_done: period_update(sim, ev_time)
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
            warmup_event(sim)
        elif ev_type == "batch":
            batch_event(sim)
        elif ev_type == "endsim":
            break
    return sim


if __name__ == "__main__":
    def ci_hw(lst):
        lst = [x for x in lst if x == x]
        n = len(lst)
        if n < 2: return float('nan')
        m = mean(lst)
        s = math.sqrt(sum((x - m) ** 2 for x in lst) / (n - 1))
        return 2.04523 * s / math.sqrt(n)


    def print_res(label, lst, scale=1., unit=""):
        m = mean(lst)
        hw = ci_hw(lst)
        print(f"  {label}: {m * scale:.4f}{unit}  95%CI=[{(m - hw) * scale:.4f},{(m + hw) * scale:.4f}]")


    print("dynamic")
    sim_dynamic = simulation(is_fixed=False)
    print_res("SC1 oh utilization", sim_dynamic.b_sc1_oh)
    print_res("SC2 oh utilization", sim_dynamic.b_sc2_oh)
    print_res("SC1 noh utilization", sim_dynamic.b_sc1_noh)
    print_res("Outpatient access time", sim_dynamic.b_op_acc, unit=" days")
    print_res("Emergency waiting time", sim_dynamic.b_em_wait, scale=60, unit=" min")
    print_res("Outpatient waiting time", sim_dynamic.b_op_wait, scale=60, unit=" min")
    print_res("Overflow fraction", sim_dynamic.b_ovfl)
    print_res("Inpatient missing", sim_dynamic.b_inp_rate)


    print("fixed")
    sim_fixed = simulation(is_fixed=True)
    print_res("SC1 oh utilization", sim_fixed.b_sc1_oh)
    print_res("SC2 oh utilization", sim_fixed.b_sc2_oh)
    print_res("SC1 noh utilization", sim_fixed.b_sc1_noh)
    print_res("Outpatient access time", sim_fixed.b_op_acc, unit=" days")
    print_res("Emergency waiting time", sim_fixed.b_em_wait, scale=60, unit=" min")
    print_res("Outpatient waiting time", sim_fixed.b_op_wait, scale=60, unit=" min")
    print_res("Overflow fraction", sim_fixed.b_ovfl)
    print_res("Inpatient missing", sim_fixed.b_inp_rate)