from collections import OrderedDict
import os
import subprocess
import sys
import multiprocessing
import itertools


def split_seq(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))


class buffered_subprocess_handler(object):
    def __init__(self):
        self.bu = []
        
    def write(self, s):
        self.bu.append(s)

    def close(self):
        pass

    def get_stdout(self):
        self.proc = subprocess.Popen(['./cryptominisat5_simple'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        return self.proc.communicate(''.join(self.bu))[0]


class subprocess_handler(object):
    def __init__(self):
        self.proc = subprocess.Popen(['./cryptominisat5_simple'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        self.r  = self.proc.stdin

    def write(self, s):
        try:
            for i in range(0, len(s), 128):
                self.r.write(s[i:i+128])
            # self.r.write(s)
        except:
            print s
            raise

    def close(self):
        pass

    def get_stdout(self):
        return self.proc.communicate()[0]


class SATGenerator(object):
    def __init__(self, traces, maxx, maxy, maxz):

        all_coords = [traces[t][io] for t in traces for io in traces[t]]
        duped_coords = list(all_coords) ; [duped_coords.remove(t) for t in set(all_coords)]
        assert len(set(all_coords)) == len(all_coords), 'coords duplicated: {}'.format(duped_coords)

        self.maxx = maxx
        self.maxy = maxy
        self.maxz = maxz
        self.xrange = range(self.maxx)
        self.yrange = range(self.maxy)
        self.zrange = range(self.maxz)

        self.vars_per_plane = maxx * maxy

        self.output_path = 'output.cnf'
        self.vars = []
        self.traces = traces
        self.traces_keys = self.traces.keys()
        self.toti = (len(self.traces) * self.maxx * self.maxy * self.maxz)
        self.tot = float(len(self.traces) * self.maxx * self.maxy * self.maxz)


        self.setup_output()
        print('setup output done')
        print('creating vars')
        self.create_vars()
        print('creating clauses')
        self.create_clauses()
        print('solving')
        self.solve()

    def setup_output(self):
        # self.output = open(self.output_path, 'w')
        #self.output = buffered_subprocess_handler()
        self.output = subprocess_handler()
        self.output.write('p cnf 0 0{}'.format(os.linesep))

    def solve(self):
        self.output.close()
        # proc = subprocess.Popen(['./cryptominisat5', self.output_path], stdout=subprocess.PIPE)
        # stdout, stderr = self.proc.communicate()
        stdout = self.output.get_stdout()
        stdout = stdout.strip()
        with open('solver_out', 'w') as so:
            so.write(stdout)
        if stdout.endswith('UNSATISFIABLE'):
            print 'FAILED'
            sys.exit(1)
        else:
            print('solved')
            sol = []
            for line in  stdout.split('\n'):
                if not line.startswith('v'):
                    continue
                # print 'line is: {}'.format(line)
                for chunk in line[1:].split():
                    #   print chunk
                    if not chunk.startswith('-') and not chunk.strip() == '0':
                        m, x, y, z, trace =  self.vars[int(chunk)-1]
                        sol.append((trace, x, y, z))
                        print m
            o = open('sol_out', 'w')
            l = ''
            for trace in list(self.traces) + ['SE']:
                if len(trace) > len(l):
                    l = trace
            l = len(l)

            for trace in self.traces:
                o.write('\n trace OUT\n')
                for z in range(self.maxz):
                    o.write('Z {}\n'.format(z))
                    for x in range(self.maxx):
                        for y in range(self.maxy):
                    #for x in self.locations_traces[trace]:
                    #    for y in self.locations_traces[trace][x]:
                            if (trace, x, y, z) in self.start_end:
                                o.write('SE{} '.format(' ' * (l - 2)))
                            elif (trace, x, y, z) in sol:
                                o.write('{}{} '.format(trace, ' ' * (l - len(trace))))
                            else:
                                o.write('0{} '.format(' ' * (l - 1)))
                        o.write('\n')
                    o.write('\n')
            o.close()

    def var(self, name):
        self.vars.append(name)
        return self.num_vars

    @property
    def num_vars(self):
        return len(self.vars)

    def locations_traces(self, trace, x, y, z):
        traces_offset = (self.vars_per_plane * self.maxz * self.traces_keys.index(trace))
        z_offset = z
        per_plane_offsett = (y ) + ((self.maxz-1)*y) + z + (x * self.maxy * self.maxz)

        ret = traces_offset  + per_plane_offsett + 1
        #self.locations_traces_check(trace, x, y, z, ret,traces_offset,z_offset,per_plane_offsett)
        return ret

    def locations_traces_check(self, trace, x, y, z, other,traces_offset, z_offset, per_plane_offsett):
        i=0
        for _trace in self.traces_keys:
            # print('{} '.format(_trace))
            # trace_xyz = OrderedDict()
            for _x in range(self.maxx):
                # ys = OrderedDict()
                for _y in range(self.maxy):
                    # zs = OrderedDict()
                    for _z in range(self.maxz):
                        # print('{} {} {} {}     {}'.format(_trace, _x, _y, _z, i))
                        i+=1
                        if (trace, x, y, z) == (_trace, _x, _y, _z):
                            assert i == other, '\nx {} y {} z {}\ni {} - other {} - traces_offset {} - z_offset {} - per_plane_offsett {}\n _trace {} trace {}'.format(_x, _y, _z, i, other,traces_offset, z_offset, per_plane_offsett, _trace, trace)
                            break
                        
            # break
        # print('done check')
        # sys.exit(1)

    def create_vars(self):
        # setup location grid
        # self.locations_traces = OrderedDict()
        for trace in self.traces:
            # trace_xyz = OrderedDict()
            for x in self.xrange:
                # ys = OrderedDict()
                for y in self.yrange:
                    # zs = OrderedDict()
                    for z in self.zrange:
                        v = self.var(('x {} y {} z {} was utilized by trace {}'.format(x, y, z, trace),x, y, z, trace))
            print('{}%'.format(self.locations_traces(trace, x, y, z)/self.tot))

            #             zs[z] = v
            #         ys[y] = zs
            #     trace_xyz[x] = ys
            # self.locations_traces[trace] = trace_xyz

    def create_clauses(self):
        # for every space
        print(' * one trace per voxel')
        #q = multiprocessing.Queue()
        #p = multiprocessing.Pool(4)
        def mp_worker(xs, qq):
            for x in xs:
                for y in self.yrange:
                    for z in self.zrange:
                        locs = []
                        # for every trace
                        for trace in self.traces:
                            _loc = self.locations_traces(trace, x, y, z)
                            locs.append(_loc)
                        # allow only one trace in this space
                        #self._naive_mutex_q(locs, qq)
                        self._naive_mutex(locs)
                #print('{}%'.format(self.locations_traces(self.traces_keys[0], x, y, z)/self.tot))
        mp_worker(self.xrange, None)
        #p.map(mp_worker, [(seq,q) for seq in split_seq(self.xrange, 4)])
        #while True:
        #    item = q.get()
        #    if item is None:
        #        break
        #    self.output.write(item)
                
        # for every start and end, require at least one neighbor
        print(' * start/end')
        self.start_end = []
        for trace in self.traces:
            for io in ['input', 'output']:
                x,y,z = self.traces[trace][io]
                v = self.locations_traces(trace, x, y, z)
                self.comment('{} at x {} y {} z {}'.format(io, x, y, z))
                self.clause([v])
                self._neighbor_constraint(trace, x, y, z)
                self.start_end.append((trace, x, y, z))
        #self.output.ttt= True
        print(' * neighbor per trace per voxel')
        for trace in self.traces:
            for x in self.xrange:
                for y in self.yrange:
                    for z in self.zrange:
                        if (trace, x, y, z) in self.start_end:
                            continue
                        self._two_neighbor_constraint(trace, x, y, z)
            print('{}%'.format(self.locations_traces(trace, x, y, z)/self.tot))


    def clause(self, v_list):
        svs = [str(v) for v in v_list]
        self.output.write('{} 0{}'.format(' '.join(svs), os.linesep))

    def comment(self, comment):
        self.output.write('c {}{}'.format(comment, os.linesep))

    def _kleiber_kwon(self, vs):
        pass

    def _naive_mutex_q(self, vs, q, cmdr_list=None):
        self.output.w = self.output.write
        self.output.write = q.put
        self._naive_mutex(vs, cmdr_list)
        self.output.write = self.output.w

    def _naive_mutex(self, vs, cmdr_list=None):
        self.comment('_naive_mutex to follow{}'.format(' with cmdrs {} and {}'.format(cmdr_list, vs) if cmdr_list is not None else ''))
        pre = cmdr_list if cmdr_list is not None else []
        for i, vi in enumerate(vs):
            if (i+1)>=len(vs):
                continue
            for vj in vs[i+1:]:
                self.clause((pre) + [-vi, -vj])
        self.comment('_naive_mutex finished')

    def _neighbor_constraint(self, trace, x, y, z):
        try:
            v = self.locations_traces(trace, x, y, z)
        except:
            print self.locations_traces.keys()
            raise
        # if v is utilized, then any of the following can be true
        nvs = [-v]
        ensure = 3+2+3
        # for xx in [x-1,x,x+1]:
        #     if xx<0 or xx>=self.maxx:
        #         ensure = None
        #         continue
        #     for yy in [y-1,y,y+1]:
        #         if yy<0 or yy>=self.maxy:
        #             ensure = None
        #             continue
        #         for zz in [z-1,z,z+1]:
        #             if xx<0 or xx>=self.maxx or yy<0 or yy>=self.maxy or zz<0 or zz>=self.maxz:
        #                 ensure = None
        #                 continue
        #             if x==xx and y==yy and z==zz:
        #                 continue
        #             # if x==xx and y==yy and z==zz:
        #             #     continue
        #             nvs.append(self.locations_traces[trace][xx][yy][zz])
        nvs += self._get_circumferential_locs(trace, x, y, z)
        # if ensure is not None:
        #     assert nvs == ensure+1, 'nvs was {}'.format(nvs)
        self.comment('if v {} then any neighbor for trace {} xyz {} {} {}'.format(v, trace, x, y, z))
        self.clause(nvs)
        # it can only go in one direction
        # self._naive_mutex(nvs[1:])

    def _two_neighbor_constraint(self, trace, x, y, z):
        try:
            v = self.locations_traces(trace, x, y, z)
        except:
            print self.locations_traces.keys()
            raise
        # if v is utilized, then any of the following can be true
        nvs = [-v]
        
        circumferential_locs = self._get_circumferential_locs(trace, x, y, z)
        for cl in circumferential_locs:
            others = list(circumferential_locs); others.remove(cl)
            # if v and cl, then one of the others
            self.clause([-cl, -v] + others)
            self._naive_mutex(others, cmdr_list=[-cl, -v])
            nvs.append(cl)
        
        self.comment('if v {} then any neighbor for trace {} xyz {} {} {}'.format(v, trace, x, y, z))
        self.clause(nvs)
        # it can only go in one direction
        # self._naive_mutex(nvs[1:])

    def _get_circumferential_locs(self, trace, x,y,z):
        #ensure = 3+2+3
        nvs = []

        #disallow_fortyfives = True

        for xx in [x-1,x,x+1]:
            if xx<0 or xx>=self.maxx:
                #ensure = None
                continue
            for yy in [y-1,y,y+1]:
                if yy<0 or yy>=self.maxy:
                    #ensure = None
                    continue
                for zz in [z-1,z,z+1]:
                    if xx<0 or xx>=self.maxx or yy<0 or yy>=self.maxy or zz<0 or zz>=self.maxz:
                        #ensure = None
                        continue
                    if x==xx and y==yy and z==zz:
                        continue
                    # restrict vias to vertical Z transitions only
                    if (xx!=x or yy!=y) and zz!=z:
                        continue
                    # if disallow_fortyfives:
                    if abs(xx-x) == 1 and abs(yy-y) == 1:
                        continue

                    nvs.append(self.locations_traces(trace, xx ,yy ,zz))
        #if ensure is not None:
        #    assert nvs == ensure, 'nvs was {}'.format(nvs)
        return nvs

    

# traces = OrderedDict([('t1', {'input':  (0,0,0),
#                               'output': (10,10,0)}),
#                       ('t2', {'input':  (0,10,0),
#                               'output': (10,1,0)}),
#                       ('t3', {'input':  (0,0,0),
#                               'output': (10,10,1)}),
#                       ('t4', {'input':  (1,3,0),
#                               'output': (10,4,0)})])
traces = OrderedDict([('t1', {'input':  (0,1,0),
                              'output': (10,10,0)}),
                      ('t2', {'input':  (0,10,0),
                              'output': (10,1,0)}),
                      ('t3', {'input':  (0,0,0),
                              'output': (10,10,1)}),
                      ('t4', {'input':  (1,3,0),
                              'output': (10,4,0)})])
SATGenerator(traces, maxx = 20, maxy = 20, maxz = 2)
