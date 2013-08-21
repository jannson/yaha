# -*- coding=utf-8 -*-
from operator import itemgetter
from prioritydictionary import priorityDictionary

class Graph:
    INFINITY = 100000
    UNDEFINDED = None

    def __init__(self, n, default_prob):
        self._data = {}
        self.N = n
        for i in xrange(0,n-1,1):
            self._data[i] = {}
            self._data[i][i+1] = default_prob
        self._data[n-1] = {}

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return (self._data)

    def __getitem__(self, node):
        if self._data.has_key(node):
            return self._data[node]
        else:
            return None
    
    def __iter__(self):
        return self._data.__iter__()

    def iteritems(self):
        return self._data.iteritems()
    
    def add_edge(self, node_from, node_to, cost=None):
        if not cost:
            cost = self.INFINITY

        self._data[node_from][node_to] = cost
        return
    
    def remove_edge(self, node_from, node_to, cost=None):
        if self._data[node_from].has_key(node_to):
            if not cost:
                cost = self._data[node_from][node_to]
                
                if cost == self.INFINITY:
                    return -1
                else:
                    self._data[node_from][node_to] = self.INFINITY
                    return cost
            elif self._data[node_from][node_to] == cost:
                self._data[node_from][node_to] = self.INFINITY
                
                return cost
            else:
                return -1
        else:
            return -1

def ksp_yen(graph, node_start, node_end, max_k=3):
    distances, previous = dijkstra(graph, node_start)
    #print 'distance=',distances
    #print 'previous=',previous
    
    A = [{'cost': distances[node_end], 
          'path': path(previous, node_start, node_end)}]
    B = []
    
    if not A[0]['path']: return A
    
    for k in range(1, max_k):
        for i in range(0, len(A[-1]['path']) - 1):
            node_spur = A[-1]['path'][i]
            path_root = A[-1]['path'][:i+1]
            
            edges_removed = []
            #print '\n A=', A
            for path_k in A:
                curr_path = path_k['path']
                if len(curr_path) > i and path_root == curr_path[:i+1]:
                    cost = graph.remove_edge(curr_path[i], curr_path[i+1])
                    #print 'remove ', cost, curr_path[i], curr_path[i+1]
                    if cost == -1:
                        continue
                    edges_removed.append([curr_path[i], curr_path[i+1], cost])
            
            path_spur = dijkstra(graph, node_spur, node_end)
            #print k,i,node_spur,node_end,'path_spur=',path_spur
            
            if path_spur['path']:
                path_total = path_root[:-1] + path_spur['path']
                dist_total = distances[node_spur] + path_spur['cost']
                potential_k = {'cost': dist_total, 'path': path_total}
            
                if not (potential_k in B):
                    B.append(potential_k)
            
            for edge in edges_removed:
                graph.add_edge(edge[0], edge[1], edge[2])
        
        if len(B):
            B = sorted(B, key=itemgetter('cost'))
            A.append(B[0])
            B.pop(0)
        else:
            break
    
    return A

def dijkstra(graph, node_start, node_end=None):
    distances = {}      
    previous = {}       
    Q = priorityDictionary()
    
    for v in graph:
        distances[v] = graph.INFINITY
        previous[v] = graph.UNDEFINDED
        Q[v] = graph.INFINITY
    
    distances[node_start] = 0
    Q[node_start] = 0
    
    for v in Q:
        if v == node_end: break

        for u in graph[v]:
            cost_vu = distances[v] + graph[v][u]
            
            if cost_vu < distances[u]:
                distances[u] = cost_vu
                Q[u] = cost_vu
                previous[u] = v

    if node_end:
        return {'cost': distances[node_end], 
                'path': path(previous, node_start, node_end)}
    else:
        return (distances, previous)

def path(previous, node_start, node_end):
    route = []

    node_curr = node_end    
    while True:
        route.append(node_curr)
        if previous[node_curr] == node_start:
            route.append(node_start)
            break
        elif previous[node_curr] == Graph.UNDEFINDED:
            return []
        
        node_curr = previous[node_curr]
    
    route.reverse()
    return route

# quick cut for one path
def quick_shortest(graph):
    N = graph.N-1
    distances = {} 
    previous = {}
    
    previous[0] = None
    distances[N] = 0.0

    for idx in xrange(N-1,-1,-1):
        Q = priorityDictionary()
        for x in graph[idx]:
            Q[x] = graph[idx][x] + distances[x]
        
        small = Q.smallest()
        previous[idx] = small
        distances[idx] = Q[small]
    # get path from previous 21/08/13 09:10:14
    paths = []
    paths.append(0)
    start = 0
    while start < N:
        paths.append(previous[start])
        start = previous[start]
    return (distances, paths)

