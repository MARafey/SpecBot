#include <iostream>
#include <vector>

using namespace std;

void addMatrices(vector<vector<int>> &A, vector<vector<int>> &B, vector<vector<int>> &C, int N) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            C[i][j] = A[i][j] + B[i][j];
        }
    }
}

int main() {
    int N;
    cout << "Enter the size of the matrix: ";
    cin >> N;

    vector<vector<int>> A(N, vector<int>(N)), B(N, vector<int>(N)), C(N, vector<int>(N));

    cout << "Enter elements of first matrix:\n";
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            cin >> A[i][j];
            B[i][j] = A[i][j];
        }
    }

    addMatrices(A, B, C, N);
    
    return 0;
}
