class Node:
    # value in form (i, j)
    def __init__(self, value, neighbors=None):
        self.value = value
        if neighbors is None:
            self.neighbors = []
        else:
            self.neighbors = neighbors
    
    def has_neighbors(self):
        return len(self.neighbors) != 0
    
    def number_of_neighbors(self):
        return len(self.neighbors)
    
    # edge: (value, weight), edges list of edges
    def add_neighbor(self, neighbor, weight=1):
        if neighbor not in self.neighbors:
            self.neighbors.append((neighbor, weight))
            return True     # operation was successful
        return False

    # output: value: [edge1,weight1] -> [edge2,weight2] -> ... -> None
    def __str__(self):
        #print("Node\t", str(self.value))
        string = str(self.value) + ": "
        for neighbor in self.neighbors:
            #print(neighbor[0].value)
            string += " [" + str(neighbor[0].value) + "," + str(neighbor[1]) + "] -> "
        return string + "None"
    
    

# field representation
class Graph:
    def __init__(self, nodes=None):
        if nodes is None:
            self.nodes = []
        else:
            self.nodes = nodes
    
    # node wasn't created yet
    def add_new_node(self, value, neighbors=None):
        if neighbors is not None:
            self.nodes.append(Node(value, neighbors))
        else:
            self.nodes.append(Node(value))

    # node was created before (may not be needed)
    def add_node(self, node):
        self.nodes.append(node)
    
    def find_node(self, value):
        for node in self.nodes:
            if node.value == value:
                return node
        return None

    def add_edge(self, value1, value2, weight=1):
        #print("Hoho")
        #print(len(self.nodes))
        node1 = self.find_node(value1)
        node2 = self.find_node(value2)
        #print(str(node1))
        #print(str(node2))

        if (node1 is not None) and (node2 is not None):
            #print("Not none :)")
            print(weight)
            node1.add_neighbor(node2, weight)
            node2.add_neighbor(node1, weight)
        else:   # not good
            print("Node(s) not found :(" + str(value1) + ", " + str(value2))
    
    def number_of_nodes(self):
        return len(self.nodes)
    
    def are_connected(self, value1, value2):
        node1 = self.find_node(value1)
        node2 = self.find_node(value2)

        for neighbor in node1.neighbors:
            if neighbor[0].value == node2.value:
                return True
        return False
    
    # vertices vertically
    def __str__(self):
        string = ""
        for node in self.nodes:
            #print("N", str(node))
            string += str(node) + "\n"
        return string
    
    # some additional methods need to be found
    