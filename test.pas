PROGRAM V1;
VAR
  a, b: integer;
  PROCEDURE test(f: integer);
    begin
      f := f + 10;
    end;
begin
  a := 10;
  test(a);
end.