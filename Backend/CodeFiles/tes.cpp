#include <iostream>
#include <vector>

using namespace std;

void addMatrices(vector<int> &A, int N) {
    int sum=0;
    for (int i = 0; i < N; i++) {
            sum+ = A[i];
        
    }
}

int main() {
    int N;
    cout << "Enter the size of the matrix: ";
    cin >> N;

vector<int> A(N);

    cout << "Enter elements of first matrix:\n";
    for (int i = 0; i < N; i++) {
            cin >> A[i];
      
    }
    addMatrices(A, N);

    return 0;
}
