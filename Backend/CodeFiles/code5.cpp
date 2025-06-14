#include <iostream>
#include <vector>
using namespace std;

int travelnext(vector<vector<bool>> graph, int x, int start)
{
    int count = 0;
    for (int i = 0; i < graph.size(); i++)
    {
        if (graph[x][i] == true)
        {
            if (graph[i][start] == true)
            {
                count++;
            }
        }
    }
    return count;
}

int travel(vector<vector<bool>> graph)
{
    int count = 0;

    for (int i = 0; i < graph.size(); i++)
    {
        int start = i;
        for (int j = 0; j < graph.size(); j++)
        {
            if (graph[i][j] == true && i != j)
            {
                count += travelnext(graph, j, start);
            }
        }
    }
    return count;
}

int main()
{
    int N, M;
    cin >> N >> M;
    vector<vector<bool>> graph(N, vector<bool>(N));
    for (int i = 0; i < N; i++)
    {
        for (int j = 0; j < N; j++)
        {
            graph[i][j] = false;
        }
    }

    while (M)
    {
        int a, b;
        cin >> a >> b;
        graph[a][b] = graph[b][a] = true;
        M--;
    }

    cout << travel(graph) / 6 << endl;
}