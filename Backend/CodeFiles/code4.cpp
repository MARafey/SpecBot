#include <iostream>
#include <vector>
using namespace std;

// Function to solve 0/1 Knapsack using Dynamic Programming
int knapsack(int W, vector<int>& weights, vector<int>& values, int n) {
    vector<vector<int>> dp(n + 1, vector<int>(W + 1, 0));

    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= W; w++) {
            if (weights[i - 1] <= w) {
                dp[i][w] = max(values[i - 1] + dp[i - 1][w - weights[i - 1]], dp[i - 1][w]);
            } else {
                dp[i][w] = dp[i - 1][w];
            }
        }
    }
    return dp[n][W];
}

int main() {
    int n = 4;  // Number of items
    int W = 8;  // Knapsack capacity
    vector<int> values = {10, 40, 30, 50};  // Values of items
    vector<int> weights = {5, 4, 6, 3};  // Weights of items

    cout << "Maximum value in Knapsack: " << knapsack(W, weights, values, n) << endl;

    return 0;
}
