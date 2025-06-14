#include <iostream>
#include<vector>
using namespace std;

int sum(vector<int> arr, int size) {
    int sum = 0;
    for (int i = 0; i < size; i++) {
        sum += arr[i];
    }
    return sum;
}


int main() {
    vector<int> arr;
    int size;
    cin>>size;
    arr.resize(size);
    for(int i=0;i<size;i++){
        cin>>arr[i];
    }
    sum(arr,size);
    return 0;
}
