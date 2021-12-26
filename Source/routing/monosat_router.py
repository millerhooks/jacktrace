from collections import OrderedDict, defaultdict
import os
import sys
import subprocess
from copy import deepcopy
from monosat import *
from time import time
# enable using multiple levels of dict keys automatically, even if nested levels don't yet exist
NestedDict = lambda: defaultdict(NestedDict)


class SATGenerator(object):
    def __init__(self, traces, maxx, maxy, maxz):
        self.maxx = maxx
        self.maxy = maxy
        self.maxz = maxz

        all_coords = [traces[t][io] for t in traces for io in traces[t]]
        duped_coords = list(all_coords);
        [duped_coords.remove(t) for t in set(all_coords)]
        assert len(set(all_coords)) == len(all_coords), 'coords duplicated: {}'.format(duped_coords)

        self.vars = {}
        self.edge_vars = {}
        self.edges_by_nodes = {}
        self.nodes = {}
        self.traces = traces
        self.visited_neighbor_edges = []
        self.reaches = []

        self.setup_output()
        self.create_vars()
        self.create_clauses()
        res = self.solve()
        if(res):
            self.parse_solution(res)

    def setup_output(self):
        self.m = Monosat()
        self.m.setOutputFile('solver_out2')
        self.m.init(' '.join([ '-conflict-min-cut', '-theory-order-vsids', '-decide-theories']))
        #self.m.init('-kt-preserve-order -force-distance')
        #self.m.init(' '.join( ['-verb=1', '-theory-order-vsids', '-vsids-both', '-decide-theories', '-no-decide-graph-rnd', '-lazy-maxflow-decisions', '-conflict-min-cut', '-conflict-min-cut-maxflow', '-reach-underapprox-cnf', '-adaptive-history-clear=5']))
        self.g = Graph()

    def create_vars(self):
        # setup nodes
        self.num_v = 0
        self.grid_by_xyz = {}  # OrderedDict()
        for x in range(self.maxx):
            ys = {}  # OrderedDict()
            for y in range(self.maxy):
                zs = {}  # OrderedDict()
                for z in range(self.maxz):
                    v = self.node(('x {} y {} z {} node'.format(x, y, z), (x, y, z)))
                    zs[z] = {'node': v, 'edges': [], 'xyz': (x, y, z), 'edges_xyz': NestedDict()}
                    self.num_v += 1
                ys[y] = zs
            self.grid_by_xyz[x] = ys

        # setup all possible edges
        for x in range(self.maxx):
            for y in range(self.maxy):
                for z in range(self.maxz):
                    self._neighbor_edges(x, y, z)

    def create_clauses(self):
        # go through the traces, OR the start node edges, then setup reachability to the end node
        self.start_end = []
        ios_overall = []
        for trace in self.traces:
            ix, iy, iz = self.traces[trace]['input']
            ox, oy, oz = self.traces[trace]['output']
            self.start_end.append((ix, iy, iz))
            self.start_end.append((ox, oy, oz))
            input_node = self.grid_by_xyz[ix][iy][iz]
            output_node = self.grid_by_xyz[ox][oy][oz]
            ios_overall.append([input_node, output_node])

            # only one of these edges is True
            # self.clause(input_node['edges'])
            # self._naive_mutex(input_node['edges'])

            inp_circumferential_loc_nodes = self._get_circumferential_locs(ix, iy, iz)
            inp_outward_edges = [self._node_edge_to(input_node, cn) for cn in inp_circumferential_loc_nodes]
            assert sorted(input_node['edges'], key=lambda x: id(x)) == sorted(inp_outward_edges,
                                                                              key=lambda x: id(x)), '{}\n{}'.format(
                sorted(input_node['edges'], key=lambda x: id(x)), sorted(inp_outward_edges, key=lambda x: id(x)))
            inp_inward_edges = [self._node_edge_to(cn, input_node) for cn in inp_circumferential_loc_nodes]
            if any([(v in inp_inward_edges) for v in inp_outward_edges]):
                raise Exception('some outward edges were also inward, gonna cause graph problems!')
            #self.clause(inp_outward_edges + inp_inward_edges)
            #self.clause(inp_outward_edges + inp_inward_edges)
            #AssertNor(*inp_inward_edges)
            #AssertAtMostOne(inp_outward_edges +inp_inward_edges)
            #AssertAtMostOne(inp_inward_edges)


            #AssertEqualPB(inp_outward_edges, 1)
            #AssertEqualPB(inp_inward_edges, 0)
            #AssertNor(inp_inward_edges)
            # Assert(Not(inp_inward_edges))


            #######
            outp_circumferential_loc_nodes = self._get_circumferential_locs(ox, oy, oz)
            outp_outward_edges = [self._node_edge_to(output_node, cn) for cn in outp_circumferential_loc_nodes]
            outp_inward_edges = [self._node_edge_to(cn, output_node) for cn in outp_circumferential_loc_nodes]
            if any([(v in outp_inward_edges) for v in outp_outward_edges]):
                raise Exception('some outward edges were also inward, gonna cause graph problems!')
            #self.clause(outp_inward_edges + outp_outward_edges)
            #AssertNor(*outp_outward_edges)
            #AssertAtMostOne(outp_inward_edges + outp_outward_edges)
            #AssertAtMostOne(outp_outward_edges)


            #AssertEqualPB(outp_inward_edges, 1)
            # print(outp_outward_edges)
            #AssertEqualPB(outp_outward_edges, 0)
            #AssertNor(outp_outward_edges)

            # self._naive_mutex([self._node_edge_to(cn, output_node) for cn in circumferential_loc_nodes])
            # new var for the clause of reachability between two nodes (start and end)
            # rv = self.var('reach {}'.format(trace))
            # reach <graphID> node1 node2 var
            # self.output.write('reach 0 {} {} {}\n'.format(ios[0]['node'], ios[1]['node'], rv))
            inp_node = input_node['node']
            outp_node = output_node['node']
            rv = self.g.reaches(inp_node, outp_node)
            self.reaches.append(rv)
            # the var is True
            #self.clause([rv])
            Assert(rv)
            if trace == 't4':
                print('t4 dist 10')
                #dist = self.g.distance_lt(inp_node, outp_node, 12)
                #Assert(dist)

            #rv = self.g.reaches(output_node['node'], input_node['node'])
            # the var is True
            #self.clause([Not(rv)])
            #Assert(Not(rv))
            #AssertNor(rv)

        # # for every space
        # all_edges = set()
        numv = 0
        p = one_percent = int(self.num_v / 100.0)

        for x in range(self.maxx):
            for y in range(self.maxy):
                for z in range(self.maxz):
                    numv += 1
                    if (numv >= p):
                        p += one_percent
                        print('{} of {}'.format(numv, self.num_v))
                    # p = self.num_v
                    if (x, y, z) in self.start_end:
                        continue
                    # for e in self.grid_by_xyz[x][y][z]['edges']:
                    #     all_edges.add(e)
                    # self._neighbor_constraint2(x,y,z)
                    for cl_node in self._get_circumferential_locs(x, y, z):
                        starting_edge = self._node_edge_to(self.grid_by_xyz[x][y][z], cl_node)
                        self._neighbor_constraint(self.grid_by_xyz[x][y][z], cl_node, starting_edge)
                        # for edge_vars_for_direction in zip(*locs):
                        #     # allow only one trace's edge
                        #     self._naive_mutex(edge_vars_for_direction)
        # the following line should be handled by the neighbor clauses, falling like dominoes from the start edges
        # self.clause(all_edges)


        # _false = self.var('false'.format(trace))
        # self.clause([Not(_false)])
        # _true = self.var('true')
        # self.clause([_true])

        # # disallow an input to connect to any other trace's output
        for ios in ios_overall:
            inp = ios[0]
            # get all other traces beside this current one
            others = list(ios_overall);
            others.remove(ios)
            # get all other traces' outputs
            other_outputs = [other_io[1] for other_io in others]
            for other_out in other_outputs:
                # self.output.write('reach 0 {} {} {}\n'.format(inp['node'], other_out['node'], _false))
                rv = self.g.reaches(inp['node'], other_out['node'])
                #self.clause([Not(rv)])
                AssertNor(rv)

        # self.output.write('acyclic 0 {}\n'.format(_true))
        Assert(self.g.acyclic())

    def solve(self):
        print('num nodes {} num edges {} num vars {}'.format(len(self.nodes), len(self.edge_vars), self.num_v))
        start_time = time()
        result = Solve()
        elapsed = time()-start_time
        if(not result):
            print("Constraints are UNSAT")
        else:
            print('Found solution in %d seconds'%(elapsed))

        return result

    def parse_solution(self, res):
        """ for a given trace, walk all edges and save them in a grid for easy printing """

        for rv in self.reaches:
            #If the result is SAT, you can find the nodes that make up a satisfying path:
            path_by_nodes = self.g.getPath(rv)
            print("Satisfying path (as a list of nodes): " +str(path_by_nodes))
        # find the longest trace name
        l = ''
        for trace in list(self.traces) + ['*']:
            if len(trace) > len(l):
                l = trace
        # store the length of the longest trace name
        l = len(l)

        # open a new file to print the readable solution to
        o = open('sol_out', 'w')

        for trace in self.traces:
            out_xyz = []

            start = place = self.traces[trace]['input']
            end = self.traces[trace]['output']

            msg = 'trace: {} start: {} end: {}'.format(trace, start, end)
            o.write('\n {}\n'.format(msg))
            print(msg)

            place = self.traces[trace]['input']
            op = self.traces[trace]['output']
            journey = []
            branches = []

            while place != op:
                journey.append(place)
                ix, iy, iz = place

                try:
                    ns = [e for e in self.grid_by_xyz[ix][iy][iz]['edges'] if e.value() and self.edge_vars[e][1] not in journey]
                    n = ns[0]
                    branches += ns[1:]
                except IndexError:
                    try:
                        n = branches.pop()
                    except IndexError:
                        print('branch ended!')
                        break #Sam: added this catch, to break in the case where branches is empty above.
                place = self.edge_vars[n][1]
                if (ix, iy, iz) != self.edge_vars[n][0]:
                    print('prev {} expected prev {}'.format((ix, iy, iz), self.edge_vars[n][0]))
                jx,jy,jz = place
                print('node in journey: {}'.format(self.grid_by_xyz[jx][jy][jz]['node']))

            # now that we're done walking the graph, we can make a crude sort-of bitmap
            for z in range(self.maxz):
                o.write('Z {}\n'.format(z))
                for x in range(self.maxx):
                    for y in range(self.maxy):
                        # print a * for start/end points
                        if (x, y, z) in [start, end]:
                            o.write('*{} '.format(' ' * (l - 1)))
                        # print the trace-name for points in a trace
                        elif (x, y, z) in journey:  # self.trace_journeys[trace]['journey']:
                            o.write('{}{} '.format(trace, ' ' * (l - len(trace))))
                        # if a space is unused, print a 0
                        else:
                            o.write('0{} '.format(' ' * (l - 1)))
                    o.write('\n')
                o.write('\n')
        o.close()

    def var(self, name):
        v = Var()
        self.vars[v] = name
        return v

    def node(self, name):
        n = self.g.addNode()
        self.nodes[n] = (name)
        return n# len(self.nodes)

    def clause(self, v_list):
        #Assert(Or(*v_list))
        AssertOr(*v_list) #Sam: changed this from Assert(Or(*v_list))

    def _neighbor_edges(self, x, y, z):
        n = self.grid_by_xyz[x][y][z]
        circumferential_locs = self._get_circumferential_locs(x, y, z)
        for cl in circumferential_locs:
            ev = self._edge(n, cl)
            n['edges'].append(ev)
            xx, yy, zz = cl['xyz']
            n['edges_xyz'][xx][yy][zz] = ev

    def _node_edge_to(self, n, on):
        x, y, z = on['xyz']
        edge = n['edges_xyz'][x][y][z]
        assert len([n['edges_xyz'][xx][yy][zz] for xx in n['edges_xyz'] for yy in n['edges_xyz'][xx] for zz in
                    n['edges_xyz'][xx][yy]]) == len(n['edges'])
        return edge

    def _neighbor_constraint(self, from_node, center_node, edge_came_from):
        # if (from_node, center_node) in self.visited_neighbor_edges or (center_node, from_node) in self.visited_neighbor_edges:
        #    return False
        # if center_node['xyz'] in [self.traces[t]['output'] for t in self.traces]:
        #     return False
        # self.visited_neighbor_edges.append((from_node, center_node))

        circumferential_loc_nodes = self._get_circumferential_locs(*center_node['xyz'])
        if from_node not in circumferential_loc_nodes:
            raise Exception('{} {}'.format(circumferential_loc_nodes, from_node))
        assert self._node_edge_to(from_node, center_node) == edge_came_from, 'uh oh'
        circumferential_loc_nodes.remove(from_node)
        # if the edge_came_from is True, then one of the outgoing edges is True
        outgoing_edges = [self._node_edge_to(center_node, n) for n in circumferential_loc_nodes]
        self.clause([Not(edge_came_from)] + outgoing_edges)# + [self._node_edge_to(n, center_node) for n in circumferential_loc_nodes])
        AssertAtMostOne(outgoing_edges)

        # TODO why is the next line causing output to be weird?
        #circumferential_loc_nodes = self._get_circumferential_locs(*center_node['xyz'])
        #AssertAtMostOne([self._node_edge_to(center_node, n) for n in circumferential_loc_nodes])
        #AssertAtMostOne([edge_came_from] + [self._node_edge_to(n, center_node) for n in circumferential_loc_nodes])
        #AssertAtMostOne([self._node_edge_to(n, center_node) for n in circumferential_loc_nodes])

        # Assert(Or(Not(v[1]), *es))

    def _edge(self, _from, _to):
        """edge <GraphID> <from> <to> <CNF Variable> [weight]"""
        # self.output.write('edge {} {} {} {} {}\n'.format(graph_id, _from, _to, v, w if w>1 else ''))
        if (_from['node'], _to['node']) in self.edges_by_nodes:
            raise Exception('we already saw this edge!')
        v = self.g.addEdge(_from['node'], _to['node'])
        self.edge_vars[v] = (_from['xyz'], _to['xyz'])
        self.edges_by_nodes[(_from['node'], _to['node'])] = v
        return v

    def _get_circumferential_locs(self, x, y, z):
        # up, down (in Z), left, right, ahead, behind (in-plane), diags
        ensure = 2 + 4 + 4
        # up, down (in Z), left, right, ahead, behind (in-plane)
        ensure = 2 + 4
        nvs = []

        disallow_fortyfives = True

        for xx in [x - 1, x, x + 1]:
            if xx < 0 or xx >= self.maxx:
                ensure = None
                continue
            for yy in [y - 1, y, y + 1]:
                if yy < 0 or yy >= self.maxy:
                    ensure = None
                    continue
                for zz in [z - 1, z, z + 1]:
                    if xx < 0 or xx >= self.maxx or yy < 0 or yy >= self.maxy or zz < 0 or zz >= self.maxz:
                        ensure = None
                        continue

                    # skip the center point (don't count the point passed into this method)
                    if x == xx and y == yy and z == zz:
                        continue

                    # restrict vias to vertical Z transitions only
                    # if Z is changing, AND x or y is too, we gotta skip it..
                    # Z can only change when going directly up or down
                    if zz != z and (xx != x or yy != y):
                        continue

                    # forty-five degree angles are disabled for now
                    # they can be enabled when diagonally crossing edges are disallowed
                    if disallow_fortyfives:
                        if abs(xx - x) == 1 and abs(yy - y) == 1:
                            continue

                    try:
                        nvs.append(self.grid_by_xyz[xx][yy][zz])
                    except:
                        print('{} {} {}'.format(xx, yy, zz))
                        raise
        if ensure is not None:
            assert len(nvs) == ensure, 'nvs was {}'.format(nvs)
        return nvs

x=12
y=12
z=2
simple = False
if simple:
    # make up some start and end points, to be placed within a grid of size: 20 x 20 x 2
    traces = OrderedDict([('t1', {'input': (3, 3, 1),
                                  'output': (10, 10, 0)}),
                          ('t2', {'input': (0, 10, 0),
                                  'output': (10, 1, 0)}),
                          ('t3', {'input': (0, 0, 0),
                                  'output': (10, 10, 1)}),
                          ('t4', {'input': (1, 3, 0),
                                  'output': (10, 4, 0)})])
else:
    # make some inputs on the left, with outputs on the right (or in the other axis, top to bottom)
    traces = OrderedDict()
    do_y = False
    if do_y:
        for iy in range(y):
            traces['t{}'.format(iy)] = {'input': (0,iy, 0), 'output': (x-1,iy, 0)}
    else:
        for ix in range(x):
            traces['t{}'.format(ix)] = {'input': (ix,0, 0), 'output': (ix,y-1, 0)}
# traces = OrderedDict([('t1', {'input': (0, 0, 0),
#                               'output': (2, 2, 0)})])
# pass the traces and the grid size, it begins to generate clauses and proceed to call the solver
SATGenerator(traces, maxx=x, maxy=y, maxz=z)
# SATGenerator(traces, maxx=3, maxy=3, maxz=1)

# diff pairs --
# if i am going forward, then buddy's candidate edges have to be parallel...
#  OR if i am doing L shape, then my buddy can do an offset L shape
