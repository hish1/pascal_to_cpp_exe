int a;
int b;

void test(int f) {
   f = f + 10;
}

int main(){
   a = 10;
   test(a);
   return 0;
}