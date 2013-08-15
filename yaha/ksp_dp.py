# -*- coding=utf-8 -*-
from operator import itemgetter
from prioritydictionary import priorityDictionary

class Graph:
    INFINITY = 10000
    UNDEFINDED = None

    def __init__(self, n):
        self._data = {}
        self.N = n
        for i in xrange(0,n,1):
            self._data[i] = {}

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
    
    def add_edge(self, node_from, node_to, cost=None):
        if not cost:
            cost = self.INFINITY

        self._data[node_to][node_from] = cost
        return
    
    def remove_edge(self, node_from, node_to, cost=None):
        if self._data[node_to].has_key(node_from):
            if not cost:
                cost = self._data[node_to][node_from]
                
                if cost == self.INFINITY:
                    return -1
                else:
                    self._data[node_to][node_from] = self.INFINITY
                    return cost
            elif self._data[node_to][node_from] == cost:
                self._data[node_to][node_from] = self.INFINITY
                
                return cost
            else:
                return -1
        else:
            return -1

def ksp_yen(graph, node_start, node_end, max_k=3):
    distances, previous = dp_graph(graph, node_start)
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
            
            path_spur = dp_graph(graph, node_spur, node_end)
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

def dp_graph(graph, node_start, node_end=None):
    N = graph.N
    distances = {} 
    previous = {}
    
    previous[node_start] = None
    for idx in xrange(0, node_start+1, 1):
        distances[idx] = 0.0

    for idx in xrange(node_start+1,N,1):
        Q = priorityDictionary()
        for x in graph[idx]:
            Q[x] = distances[x] + graph[idx][x]
        small = Q.smallest()
        if small < node_start:
            previous[idx] = node_start
        else:
            previous[idx] = Q.smallest()
        distances[idx] = Q[small]
    
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
